"""
AI/LLM business logic: forecast explanation, intent extraction, scenario narration.
Falls back gracefully to templates when OPENAI_API_KEY is absent.
Supports English, Hinglish, and Hindi.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Dict, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

# Load .env from project root
from pathlib import Path
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_project_root / ".env")

logger = logging.getLogger("walletgo.ai")

_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
_client: Optional[object] = OpenAI(api_key=_api_key) if OpenAI and _api_key else None
_model = "gpt-4o-mini"


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
        response = _client.chat.completions.create(
            model=_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You explain personal finance forecasts clearly and briefly. "
                        f"Reply in {_language_name(language)}."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Explain this forecast in simple terms: {forecast}",
                },
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_explanation(forecast, language)


def extract_scenario_intent(user_input: str, language: str = "en") -> Dict:
    normalized = user_input.lower().strip()
    amount_match = re.search(r"(?:[$₹]\s*)?([0-9][0-9,]*(?:\.[0-9]+)?)", normalized)
    amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0.0

    intent = "spend"
    if any(kw in normalized for kw in ["save", "skip", "avoid", "delay"]):
        intent = "save"
    elif any(kw in normalized for kw in ["salary", "income", "payday", "deposit"]):
        intent = "income"

    if "delay" in normalized or "late" in normalized:
        intent = "delay"

    return {
        "intent": intent,
        "amount": amount,
        "currency": "USD",
        "description": user_input,
        "language": language,
    }


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
