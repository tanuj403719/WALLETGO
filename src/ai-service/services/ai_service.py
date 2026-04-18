"""
AI/LLM business logic: forecast explanation, intent extraction, scenario narration.
Falls back gracefully to templates when GEMINI_API_KEY is absent.
Supports English, Hinglish, and Hindi.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except Exception:  # pragma: no cover
    genai = None
    GenerationConfig = None

# Load .env from project root
from pathlib import Path
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_project_root / ".env")

logger = logging.getLogger("walletgo.ai")

_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
_model_name: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if genai and _api_key:
    try:
        genai.configure(api_key=_api_key)
        _client: Optional[object] = genai.GenerativeModel(_model_name)
    except Exception:
        logger.exception("Failed to initialize Gemini client")
        _client = None
else:
    _client = None


def _extract_text(response: Any) -> str:
    """Safely read text from Gemini responses across SDK variants."""
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if isinstance(part_text, str) and part_text.strip():
                return part_text.strip()

    return ""


def is_llm_available() -> bool:
    return _client is not None


def _language_name(language: str) -> str:
    return {"en": "English", "hinglish": "Hinglish", "hi": "Hindi"}.get(language, "English")


def _fallback_explanation(forecast: Dict, language: str = "en") -> str:
    """Template-based explanation used when no LLM is available."""
    forecast_points = forecast.get("forecast_data", [])
    if not forecast_points:
        return "No forecast data is available yet."

    minimum_point = min(forecast_points, key=lambda item: item.get("balance", 0))
    balance = round(float(minimum_point.get("balance", 0)), 2)
    date = minimum_point.get("date", "the forecast window")
    confidence = round(float(forecast.get("confidence", 0)), 0)

    if language == "hinglish":
        return (
            f"Agle few weeks mein sabse low balance {date} ko around ${balance} dikhta hai. "
            f"Confidence {confidence}% hai, isliye kuch buffer rakhna sensible rahega."
        )
    if language == "hi":
        return (
            f"अगले कुछ हफ्तों में सबसे कम बैलेंस {date} के आसपास ${balance} दिख रहा है। "
            f"Confidence {confidence}% है, इसलिए थोड़ा buffer रखना बेहतर होगा।"
        )
    return (
        f"The lowest projected balance occurs on {date} at about ${balance}. "
        f"Confidence is {confidence}%, so there is enough signal to act, but keep a buffer for safety."
    )


def generate_explanation(forecast: Dict, language: str = "en") -> str:
    if not _client:
        return _fallback_explanation(forecast, language)

    try:
        prompt = (
            "You explain personal finance forecasts clearly and briefly. "
            f"Reply in {_language_name(language)}. "
            f"Explain this forecast in simple terms: {forecast}"
        )
        response = _client.generate_content(
            prompt,
            generation_config=GenerationConfig(temperature=0.4),
        )
        content = _extract_text(response)
        return content or _fallback_explanation(forecast, language)
    except Exception:
        return _fallback_explanation(forecast, language)


def extract_scenario_intent(
    user_input: str,
    language: str = "en",
    transaction_context: Optional[Dict[str, Any]] = None,
) -> Dict:
    """
    Parse free-form what-if text into structured financial events.

    Returns a dictionary containing at least an `events` array, where each event has:
    - type: one_time_spend | one_time_income | recurring_spend | recurring_income
    - amount: float
    - date_offset_days: int
    - duration_days: int | null (optional, for temporary recurring effects)
    - description: str
    """

    if _client:
        parsed = _extract_scenario_events_llm(user_input, language, transaction_context)
        if parsed:
            return parsed

    fallback = _extract_scenario_events_fallback(user_input, language, transaction_context)
    if _client:
        fallback["fallback_reason"] = "gemini_request_failed_or_quota_exceeded"
        fallback["model"] = _model_name
    else:
        fallback["fallback_reason"] = "gemini_not_configured"
    return fallback


def _extract_scenario_events_llm(
    user_input: str,
    language: str,
    transaction_context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Use LLM JSON mode to extract scenario events."""
    assert _client is not None
    system_prompt = (
        "You extract personal finance what-if events into strict JSON. "
        "Return only a JSON object with key 'events'. "
        "Each events item must include: "
        "type (one_time_spend|one_time_income|recurring_spend|recurring_income), "
        "amount (float > 0), date_offset_days (int >= 0), description (string). "
        "Optional: duration_days (int > 0) for temporary recurring events. "
        "Interpret relative dates from today. If unspecified, use 0. "
        "If weekly recurring, encode monthly-equivalent amount when possible. "
        "Use transaction_context if provided to estimate realistic amounts when user omits numbers. "
        "For temporary spend cuts (for N days/weeks), prefer recurring_income with duration_days. "
        "Never return markdown."
    )

    try:
        prompt = (
            f"{system_prompt}\n"
            f"Input JSON: {json.dumps({'language': language, 'text': user_input, 'transaction_context': transaction_context or {}}, ensure_ascii=False)}"
        )
        response = _client.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )

        content = _extract_text(response).strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        payload = json.loads(content)
        events = _sanitize_events(payload.get("events", []), user_input)
        if not events:
            return None
        return {
            "events": events,
            "description": user_input,
            "language": language,
            "parser": "gemini",
            "model": _model_name,
        }
    except Exception:
        logger.exception("LLM scenario extraction failed; using fallback parser")
        return None


def _sanitize_events(raw_events: Any, raw_text: str) -> List[Dict[str, Any]]:
    """Normalize untrusted LLM output into strict event schema."""
    allowed_types = {
        "one_time_spend",
        "one_time_income",
        "recurring_spend",
        "recurring_income",
    }
    if not isinstance(raw_events, list):
        return []

    sanitized: List[Dict[str, Any]] = []
    for item in raw_events:
        if not isinstance(item, dict):
            continue

        event_type = str(item.get("type") or "").strip().lower()
        if event_type not in allowed_types:
            continue

        try:
            amount = float(item.get("amount", 0.0))
        except (TypeError, ValueError):
            continue
        amount = abs(amount)
        if amount <= 0:
            continue

        try:
            date_offset_days = int(item.get("date_offset_days", 0))
        except (TypeError, ValueError):
            date_offset_days = 0
        date_offset_days = max(date_offset_days, 0)

        raw_duration_days = item.get("duration_days")
        duration_days = None
        if raw_duration_days is not None:
            try:
                parsed_duration = int(raw_duration_days)
                if parsed_duration > 0:
                    duration_days = parsed_duration
            except (TypeError, ValueError):
                duration_days = None

        description = str(item.get("description") or raw_text).strip() or raw_text
        sanitized.append(
            {
                "type": event_type,
                "amount": round(amount, 2),
                "date_offset_days": date_offset_days,
                "duration_days": duration_days,
                "description": description,
            }
        )

    return sanitized


def _extract_duration_days(normalized_text: str) -> Optional[int]:
    days_match = re.search(r"for\s+([0-9]{1,3})\s+days?", normalized_text)
    if days_match:
        return max(int(days_match.group(1)), 1)

    weeks_match = re.search(r"for\s+([0-9]{1,2})\s+weeks?", normalized_text)
    if weeks_match:
        return max(int(weeks_match.group(1)) * 7, 1)

    return None


def _looks_like_spend_reduction(normalized_text: str) -> bool:
    reduction_terms = ["don't", "dont", "no", "skip", "avoid", "cut", "reduce", "stop"]
    spend_terms = ["shop", "shopping", "spend", "coffee", "food", "dining", "subscription"]
    return any(term in normalized_text for term in reduction_terms) and any(
        term in normalized_text for term in spend_terms
    )


def _context_daily_spend(transaction_context: Optional[Dict[str, Any]]) -> float:
    if not isinstance(transaction_context, dict):
        return 60.0
    try:
        value = float(transaction_context.get("median_daily_spend", 60.0) or 60.0)
    except (TypeError, ValueError):
        value = 60.0
    return max(10.0, min(250.0, value))


def _estimate_cut_daily_amount(normalized_text: str, transaction_context: Optional[Dict[str, Any]]) -> float:
    explicit = re.search(r"(?:\$|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:/|per)\s*day", normalized_text)
    if explicit:
        return max(5.0, min(200.0, float(explicit.group(1))))

    baseline = _context_daily_spend(transaction_context)
    multiplier = 0.30
    if any(k in normalized_text for k in ["coffee", "tea", "cafe"]):
        multiplier = 0.10
    elif any(k in normalized_text for k in ["subscription", "netflix", "spotify", "prime"]):
        multiplier = 0.12
    elif any(k in normalized_text for k in ["food", "dining", "restaurant"]):
        multiplier = 0.20
    elif any(k in normalized_text for k in ["shop", "shopping", "amazon", "flipkart"]):
        multiplier = 0.35

    return max(8.0, min(150.0, round(baseline * multiplier, 2)))


def _extract_scenario_events_fallback(
    user_input: str,
    language: str,
    transaction_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Regex/date-keyword fallback extraction for one or more events."""
    splitter = r"\b(?:but|and|also|plus)\b"
    original_clauses = [c.strip() for c in re.split(splitter, user_input, flags=re.IGNORECASE) if c.strip()]
    normalized_clauses = [c.lower() for c in original_clauses]

    events: List[Dict[str, Any]] = []
    for original_clause, normalized in zip(original_clauses, normalized_clauses):
        amount_match = re.search(r"(?:[$₹]\s*)?([0-9][0-9,]*(?:\.[0-9]+)?)", normalized)
        amount = 0.0
        if amount_match:
            suffix = normalized[amount_match.end() : amount_match.end() + 16]
            # Avoid treating duration counts like "10 days" as money amounts.
            looks_like_duration_number = bool(re.match(r"\s*(day|days|week|weeks|month|months)\b", suffix))
            if not looks_like_duration_number:
                amount = float(amount_match.group(1).replace(",", ""))

        if amount <= 0 and _looks_like_spend_reduction(normalized):
            duration_days = _extract_duration_days(normalized) or 14
            daily_cut = _estimate_cut_daily_amount(normalized, transaction_context)
            monthly_equivalent = round(daily_cut * 30.5, 2)
            events.append(
                {
                    "type": "recurring_income",
                    "amount": monthly_equivalent,
                    "date_offset_days": _extract_offset_days(normalized),
                    "duration_days": duration_days,
                    "description": original_clause,
                }
            )
            continue

        if amount <= 0:
            continue

        is_weekly = any(kw in normalized for kw in ["every week", "weekly", "per week", "a week"]) 
        is_monthly = any(kw in normalized for kw in ["every month", "monthly", "per month", "a month", "each month"])
        is_recurring = is_weekly or is_monthly

        income_keywords = ["salary", "income", "payday", "deposit", "bonus", "save", "saving", "skip", "avoid", "refund"]
        spend_keywords = ["buy", "spend", "purchase", "pay", "bill", "rent", "grocer", "laptop", "phone", "trip", "flight"]

        if any(kw in normalized for kw in spend_keywords) and not any(kw in normalized for kw in ["save", "skip", "avoid"]):
            event_type = "recurring_spend" if is_recurring else "one_time_spend"
        elif any(kw in normalized for kw in income_keywords):
            event_type = "recurring_income" if is_recurring else "one_time_income"
        else:
            event_type = "recurring_spend" if is_recurring else "one_time_spend"

        if is_weekly:
            # Forecast service treats recurring amount as monthly-equivalent for daily amortization.
            amount = amount * 4.35

        events.append(
            {
                "type": event_type,
                "amount": round(abs(amount), 2),
                "date_offset_days": _extract_offset_days(normalized),
                "duration_days": _extract_duration_days(normalized) if event_type.startswith("recurring") else None,
                "description": original_clause,
            }
        )

    if not events:
        events = [
            {
                "type": "one_time_spend",
                "amount": 0.0,
                "date_offset_days": 0,
                "description": user_input,
            }
        ]

    return {
        "events": [event for event in events if event.get("amount", 0.0) > 0],
        "description": user_input,
        "language": language,
        "parser": "fallback",
    }


def _extract_offset_days(normalized_text: str) -> int:
    """Infer relative date offsets from simple natural language cues."""
    if "next week" in normalized_text:
        return 7
    if "in two weeks" in normalized_text or "2 weeks" in normalized_text:
        return 14
    if "tomorrow" in normalized_text:
        return 1

    weeks_match = re.search(r"in\s+([0-9]{1,2})\s+weeks?", normalized_text)
    if weeks_match:
        return max(int(weeks_match.group(1)), 0) * 7

    days_match = re.search(r"in\s+([0-9]{1,3})\s+days?", normalized_text)
    if days_match:
        return max(int(days_match.group(1)), 0)

    return 0


def generate_scenario_explanation(
    scenario_results: Dict,
    original_forecast: Dict,
    language: str = "en",
) -> str:
    likely = scenario_results.get("likely", {}).get("forecast_data", [])
    if not likely:
        return _fallback_explanation(original_forecast, language)

    def _row_balance(row: Dict[str, Any]) -> float:
        return float(row.get("predicted_balance", row.get("balance", 0.0)) or 0.0)

    minimum_point = min(likely, key=_row_balance)
    balance = round(_row_balance(minimum_point), 2)
    date = minimum_point.get("date", "the forecast window")

    base_likely = original_forecast.get("forecast_data", [])
    base_min = 0.0
    if base_likely:
        base_min = round(min(_row_balance(row) for row in base_likely), 2)

    scenario_end = round(_row_balance(likely[-1]), 2) if likely else 0.0
    base_end = round(_row_balance(base_likely[-1]), 2) if base_likely else 0.0

    min_delta = round(balance - base_min, 2)
    end_delta = round(scenario_end - base_end, 2)
    direction_min = "improves" if min_delta >= 0 else "worsens"

    if _client:
        try:
            summary = {
                "language": language,
                "scenario_min_balance": balance,
                "scenario_min_balance_date": date,
                "base_min_balance": base_min,
                "min_balance_delta": min_delta,
                "scenario_end_balance": scenario_end,
                "base_end_balance": base_end,
                "end_balance_delta": end_delta,
                "events": scenario_results.get("events", []),
            }
            prompt = (
                "You explain personal finance what-if outcomes with concrete numbers, no fluff. "
                f"Reply in {_language_name(language)}. "
                "Use these facts and explain impact in 2-3 sentences, including what changed vs base forecast: "
                f"{json.dumps(summary, ensure_ascii=False)}"
            )
            response = _client.generate_content(
                prompt,
                generation_config=GenerationConfig(temperature=0.2),
            )
            content = _extract_text(response)
            if content:
                return content
        except Exception:
            logger.exception("LLM scenario explanation failed; using deterministic fallback")

    if language == "hinglish":
        return (
            f"Is scenario mein minimum balance {date} ko ${balance} aata hai, jo base se ${abs(min_delta)} {direction_min} karta hai. "
            f"Forecast window ke end tak net impact लगभग ${end_delta} hai."
        )
    if language == "hi":
        return (
            f"इस scenario में न्यूनतम बैलेंस {date} को ${balance} है, जो base की तुलना में ${abs(min_delta)} {direction_min} करता है। "
            f"Forecast window के अंत तक कुल प्रभाव लगभग ${end_delta} है।"
        )

    return (
        f"Under this scenario, the minimum likely balance is about ${balance} on {date}, which {direction_min} the base-case minimum by ${abs(min_delta)}. "
        f"By the end of the forecast window, net impact versus base is about ${end_delta}."
    )


def _fallback_target_balance_advice(target_plan: Dict, language: str = "en") -> str:
    target = float(target_plan.get("target_balance", 0.0) or 0.0)
    horizon_days = int(target_plan.get("horizon_days", 0) or 0)
    gap = float(target_plan.get("target_gap", 0.0) or 0.0)
    monthly_needed = float(target_plan.get("required_monthly_savings", 0.0) or 0.0)
    recommendations = target_plan.get("recommended_cuts", []) or []

    if gap <= 0:
        if language == "hi":
            return f"आप ${target:.0f} का लक्ष्य {horizon_days} दिनों में पहले से ट्रैक पर हैं। वर्तमान खर्च योजना बनाए रखें।"
        if language == "hinglish":
            return f"Aap ${target:.0f} target ke liye {horizon_days} days me already on track ho. Current spending discipline continue karo."
        return (
            f"You are already on track to reach ${target:.0f} in {horizon_days} days. "
            "Keep your current spending pattern and maintain a small safety buffer."
        )

    top_lines = []
    for item in recommendations[:3]:
        category = str(item.get("category") or "general")
        monthly_cut = float(item.get("recommended_cut_monthly", 0.0) or 0.0)
        percent = float(item.get("cut_percent", 0.0) or 0.0)
        top_lines.append((category, monthly_cut, percent))

    if language == "hi":
        if top_lines:
            first = "\n".join(
                [f"- {cat}: लगभग ${amt:.0f}/माह ({pct:.0f}% कटौती)" for cat, amt, pct in top_lines]
            )
            return (
                f"${target:.0f} लक्ष्य तक पहुंचने के लिए आपको लगभग ${monthly_needed:.0f}/माह अतिरिक्त बचत चाहिए। "
                f"अगले {horizon_days} दिनों के लिए ये कटौती करें:\n{first}"
            )
        return f"${target:.0f} लक्ष्य तक पहुंचने के लिए ${monthly_needed:.0f}/माह अतिरिक्त बचत की आवश्यकता है।"

    if language == "hinglish":
        if top_lines:
            first = "\n".join(
                [f"- {cat}: around ${amt:.0f}/month cut ({pct:.0f}% reduction)" for cat, amt, pct in top_lines]
            )
            return (
                f"${target:.0f} target hit karne ke liye approx ${monthly_needed:.0f}/month extra save karna hoga. "
                f"Agle {horizon_days} days ke liye yeh cuts try karo:\n{first}"
            )
        return f"${target:.0f} target ke liye ${monthly_needed:.0f}/month extra savings chahiye."

    if top_lines:
        first = "\n".join(
            [f"- {cat}: cut about ${amt:.0f}/month ({pct:.0f}% reduction)" for cat, amt, pct in top_lines]
        )
        return (
            f"To reach ${target:.0f} in {horizon_days} days, you need about ${monthly_needed:.0f} in extra monthly savings. "
            f"Start with these cuts:\n{first}"
        )

    return (
        f"To reach ${target:.0f} in {horizon_days} days, you need about ${monthly_needed:.0f} in extra monthly savings. "
        "Your spending history is limited, so start with discretionary categories first."
    )


def generate_target_balance_advice(
    target_plan: Dict,
    language: str = "en",
    transaction_context: Optional[Dict[str, Any]] = None,
) -> str:
    if not _client:
        return _fallback_target_balance_advice(target_plan, language)

    try:
        prompt = (
            "You are a practical personal finance coach. "
            f"Respond in {_language_name(language)}. "
            "Give concrete, short, prioritized spending-cut actions to hit the target balance. "
            "Use exact numbers from target_plan; keep it under 120 words. "
            "Mention top categories and monthly cut amounts. "
            f"target_plan={json.dumps(target_plan, ensure_ascii=False)} "
            f"transaction_context={json.dumps(transaction_context or {}, ensure_ascii=False)}"
        )
        response = _client.generate_content(
            prompt,
            generation_config=GenerationConfig(temperature=0.35),
        )
        content = _extract_text(response)
        return content or _fallback_target_balance_advice(target_plan, language)
    except Exception:
        logger.exception("Target balance advice generation failed; using fallback")
        return _fallback_target_balance_advice(target_plan, language)
