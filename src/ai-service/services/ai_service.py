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


def extract_scenario_intent(user_input: str, language: str = "en") -> Dict:
    """
    Parse free-form what-if text into structured financial events.

    Returns a dictionary containing at least an `events` array, where each event has:
    - type: one_time_spend | one_time_income | recurring_spend | recurring_income
    - amount: float
    - date_offset_days: int
    - description: str
    """

    if _client:
        parsed = _extract_scenario_events_llm(user_input, language)
        if parsed:
            return parsed

    return _extract_scenario_events_fallback(user_input, language)


def _extract_scenario_events_llm(user_input: str, language: str) -> Optional[Dict[str, Any]]:
    """Use LLM JSON mode to extract scenario events."""
    assert _client is not None
    system_prompt = (
        "You extract personal finance what-if events into strict JSON. "
        "Return only a JSON object with key 'events'. "
        "Each events item must include: "
        "type (one_time_spend|one_time_income|recurring_spend|recurring_income), "
        "amount (float > 0), date_offset_days (int >= 0), description (string). "
        "Interpret relative dates from today. If unspecified, use 0. "
        "If weekly recurring, encode monthly-equivalent amount when possible. "
        "Never return markdown."
    )

    try:
        prompt = (
            f"{system_prompt}\n"
            f"Input JSON: {json.dumps({'language': language, 'text': user_input}, ensure_ascii=False)}"
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

        description = str(item.get("description") or raw_text).strip() or raw_text
        sanitized.append(
            {
                "type": event_type,
                "amount": round(amount, 2),
                "date_offset_days": date_offset_days,
                "description": description,
            }
        )

    return sanitized


def _extract_scenario_events_fallback(user_input: str, language: str) -> Dict[str, Any]:
    """Regex/date-keyword fallback extraction for one or more events."""
    splitter = r"\b(?:but|and|also|plus)\b"
    original_clauses = [c.strip() for c in re.split(splitter, user_input, flags=re.IGNORECASE) if c.strip()]
    normalized_clauses = [c.lower() for c in original_clauses]

    events: List[Dict[str, Any]] = []
    for original_clause, normalized in zip(original_clauses, normalized_clauses):
        amount_match = re.search(r"(?:[$₹]\s*)?([0-9][0-9,]*(?:\.[0-9]+)?)", normalized)
        if not amount_match:
            continue
        amount = float(amount_match.group(1).replace(",", ""))
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

    minimum_point = min(likely, key=lambda item: item.get("balance", 0))
    balance = round(float(minimum_point.get("balance", 0)), 2)
    date = minimum_point.get("date", "the forecast window")

    if language == "hinglish":
        return (
            f"Agar yeh scenario apply karte ho, toh {date} tak likely balance ${balance} tak ja sakta hai. "
            f"Low aur high range ke beech ka gap uncertainty dikhata hai."
        )
    if language == "hi":
        return (
            f"यदि यह scenario लागू करते हैं, तो {date} तक likely balance लगभग ${balance} हो सकता है। "
            f"Low और high range के बीच का gap uncertainty दिखाता है।"
        )

    return (
        f"With this scenario, the likely balance could reach about ${balance} by {date}. "
        f"The spread between low and high outcomes shows how much uncertainty remains."
    )
