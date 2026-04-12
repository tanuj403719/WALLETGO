"""
Pydantic request schemas for the ai-service.
"""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel


class ExplainForecastRequest(BaseModel):
    forecast: Dict
    language: str = "en"


class ExtractIntentRequest(BaseModel):
    user_input: str
    language: str = "en"
    transaction_context: Optional[Dict] = None


class ScenarioExplanationRequest(BaseModel):
    scenario_results: Dict
    original_forecast: Dict
    language: str = "en"
