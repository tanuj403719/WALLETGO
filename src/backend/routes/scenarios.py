"""
Scenario proxy routes — orchestrates data-service + forecast-service + ai-service.
All routes are protected (JWT required).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from client import forward
from deps import resolve_user_id

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")
FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8001")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8002")

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


class ScenarioRequest(BaseModel):
    description: str
    language: str = "en"
    ephemeral_transactions: Optional[List[Dict[str, Any]]] = None


@router.post("/analyze")
async def analyze_scenario(request: ScenarioRequest, user_id: str = Depends(resolve_user_id)):
    # 1. Fetch transactions
    if request.ephemeral_transactions:
        transactions = request.ephemeral_transactions
    else:
        tx_data = await forward(
            "GET",
            f"{DATA_SERVICE_URL}/api/transactions/list",
            params={"user_id": user_id},
        )
        transactions = tx_data.get("items", [])

    # 2. Generate base forecast
    base_forecast = await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": 42},
    )

    # 3. Extract intent from user description
    intent = await forward(
        "POST",
        f"{AI_SERVICE_URL}/api/ai/extract-intent",
        json={"user_input": request.description, "language": request.language},
    )

    # 4. Run scenario on the base forecast
    scenario_results = await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/scenario",
        json={
            "base_forecast": base_forecast,
            "scenario": {
                "amount": intent.get("amount", 0.0),
                "type": intent.get("intent", "spend"),
                "date": base_forecast["forecast_data"][0]["date"],
            },
        },
    )

    # 5. Generate narrative explanation
    explanation = await forward(
        "POST",
        f"{AI_SERVICE_URL}/api/ai/scenario-explanation",
        json={
            "scenario_results": scenario_results,
            "original_forecast": base_forecast,
            "language": request.language,
        },
    )

    return {
        **scenario_results,
        "explanation": explanation.get("explanation", ""),
        "intent": intent,
    }


@router.get("/suggestions")
async def get_scenario_suggestions(language: str = "en", user_id: str = Depends(resolve_user_id)):
    return await forward("GET", f"{AI_SERVICE_URL}/api/ai/suggestions", params={"language": language})
