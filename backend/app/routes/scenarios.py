"""Scenario forecasting endpoints."""

from typing import Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_service import AIService
from app.services.forecast_service import ForecastService
from app.services.natwest_service import NatWestService

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])
forecast_service = ForecastService()
natwest_service = NatWestService()
ai_service = AIService()

class ScenarioRequest(BaseModel):
    description: str
    language: str = "en"  # "en", "hinglish", "hi"

class ScenarioResponse(BaseModel):
    low: Dict
    likely: Dict
    high: Dict
    explanation: str

@router.post("/analyze")
async def analyze_scenario(request: ScenarioRequest):
    """Analyze a what-if scenario."""

    base_forecast = forecast_service.generate_forecast(natwest_service.get_demo_transactions())
    intent = ai_service.extract_scenario_intent(request.description, request.language)
    scenario = {
        "amount": intent.get("amount", 0.0),
        "type": intent.get("intent", "spend"),
        "date": base_forecast["forecast_data"][0]["date"],
    }
    low, likely, high = forecast_service.run_scenario(base_forecast, scenario)
    explanation = ai_service.generate_scenario_explanation(
        {"low": low, "likely": likely, "high": high},
        base_forecast,
        request.language,
    )
    return {"low": low, "likely": likely, "high": high, "explanation": explanation, "intent": intent}

@router.get("/suggestions")
async def get_scenario_suggestions(language: str = "en"):
    """Get suggested scenarios."""

    suggestions = {
        "en": ["$500 flight", "Skip coffee 2 weeks", "Payday 3 days late"],
        "hinglish": ["$500 ka flight", "2 hafte coffee skip karo", "Salary 3 din late ho"],
        "hi": ["$500 की फ्लाइट", "2 सप्ताह कॉफी छोड़ें", "तनख्वाह 3 दिन देर से हो"],
    }
    return {"language": language, "suggestions": suggestions.get(language, suggestions["en"])}
