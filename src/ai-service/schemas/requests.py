"""
Pydantic request schemas for the ai-service.
"""

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel


class ExplainForecastRequest(BaseModel):
    forecast: Dict
    language: str = "en"


class ExtractIntentRequest(BaseModel):
    user_input: str
    language: str = "en"


class ScenarioExplanationRequest(BaseModel):
    scenario_results: Dict
    original_forecast: Dict
    language: str = "en"
