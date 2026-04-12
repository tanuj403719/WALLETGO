"""
AI HTTP endpoints: explain, extract-intent, scenario-explanation, suggestions.
"""

from __future__ import annotations

from fastapi import APIRouter

from schemas.requests import (
    ExplainForecastRequest,
    ExtractIntentRequest,
    ScenarioExplanationRequest,
)
from services.ai_service import (
    extract_scenario_intent,
    generate_explanation,
    generate_scenario_explanation,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])

_SUGGESTIONS = {
    "en": ["$500 flight", "Skip coffee 2 weeks", "Payday 3 days late"],
    "hinglish": ["$500 ka flight", "2 hafte coffee skip karo", "Salary 3 din late ho"],
    "hi": ["$500 की फ्लाइट", "2 सप्ताह कॉफी छोड़ें", "तनख्वाह 3 दिन देर से हो"],
}


@router.post("/explain")
async def api_explain_forecast(request: ExplainForecastRequest):
    explanation = generate_explanation(request.forecast, request.language)
    return {"explanation": explanation, "language": request.language}


@router.post("/extract-intent")
async def api_extract_intent(request: ExtractIntentRequest):
    return extract_scenario_intent(
        request.user_input,
        request.language,
        request.transaction_context,
    )


@router.post("/scenario-explanation")
async def api_scenario_explanation(request: ScenarioExplanationRequest):
    explanation = generate_scenario_explanation(
        request.scenario_results,
        request.original_forecast,
        request.language,
    )
    return {"explanation": explanation, "language": request.language}


@router.get("/suggestions")
async def api_suggestions(language: str = "en"):
    return {
        "language": language,
        "suggestions": _SUGGESTIONS.get(language, _SUGGESTIONS["en"]),
    }
