"""
Forecast proxy routes — orchestrates data-service + forecast-service.
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

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


class ForecastRequest(BaseModel):
    days: int = 42
    ephemeral_transactions: Optional[List[Dict[str, Any]]] = None


async def _fetch_transactions(user_id: str) -> list:
    tx_data = await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/transactions/list",
        params={"user_id": user_id},
    )
    return tx_data.get("items", [])


@router.post("/generate")
async def generate_forecast(request: ForecastRequest, user_id: str = Depends(resolve_user_id)):
    transactions = request.ephemeral_transactions or await _fetch_transactions(user_id)
    return await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": request.days},
    )


@router.get("/current")
async def get_current_forecast(user_id: str = Depends(resolve_user_id)):
    transactions = await _fetch_transactions(user_id)
    return await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": 42},
    )


@router.get("/history")
async def get_forecast_history(limit: int = 10, user_id: str = Depends(resolve_user_id)):
    transactions = await _fetch_transactions(user_id)
    return await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/history",
        json={"transactions": transactions, "limit": limit},
    )
