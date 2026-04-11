"""
Forecast proxy routes — orchestrates data-service + forecast-service.
All routes are protected (JWT required).
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from client import forward
from deps import verify_token

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")
FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8001")

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


class ForecastRequest(BaseModel):
    days: int = 42


async def _fetch_transactions() -> list:
    tx_data = await forward("GET", f"{DATA_SERVICE_URL}/api/transactions/list")
    return tx_data.get("items", [])


@router.post("/generate")
async def generate_forecast(request: ForecastRequest, user_id: str = Depends(verify_token)):
    transactions = await _fetch_transactions()
    return await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": request.days},
    )


@router.get("/current")
async def get_current_forecast(user_id: str = Depends(verify_token)):
    transactions = await _fetch_transactions()
    return await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": 42},
    )


@router.get("/history")
async def get_forecast_history(limit: int = 10, user_id: str = Depends(verify_token)):
    transactions = await _fetch_transactions()
    return await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/history",
        json={"transactions": transactions, "limit": limit},
    )
