"""Forecast endpoints."""

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.forecast_service import ForecastService
from app.services.natwest_service import NatWestService

router = APIRouter(prefix="/api/forecast", tags=["forecast"])
forecast_service = ForecastService()
natwest_service = NatWestService()

class ForecastRequest(BaseModel):
    days: int = 42

class ForecastResponse(BaseModel):
    forecast_data: List[dict]
    confidence: float
    min_balance: float
    min_balance_date: str

@router.post("/generate")
async def generate_forecast(request: ForecastRequest):
    """Generate 6-week forecast."""

    transactions = natwest_service.get_demo_transactions()
    return forecast_service.generate_forecast(transactions, request.days)

@router.get("/current")
async def get_current_forecast():
    """Get current user's forecast."""

    transactions = natwest_service.get_demo_transactions()
    return forecast_service.generate_forecast(transactions)

@router.get("/history")
async def get_forecast_history(limit: int = 10):
    """Get forecast history."""

    transactions = natwest_service.get_demo_transactions()
    return {"items": [forecast_service.generate_forecast(transactions, 14) for _ in range(min(limit, 3))]}
