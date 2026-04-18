"""
Forecast proxy routes — orchestrates data-service + forecast-service.
All routes are protected (JWT required).
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from client import forward
from deps import resolve_user_id

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")
FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8001")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8002")

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


class ForecastRequest(BaseModel):
    days: int = 42
    ephemeral_transactions: Optional[List[Dict[str, Any]]] = None


class GoalForecastRequest(BaseModel):
    target_amount: float
    target_date: str  # ISO date: YYYY-MM-DD
    language: str = "en"
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


def _aggregate_category_spending(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
    """Group expenses by category, normalised to monthly spend."""
    raw: Dict[str, float] = {}
    dates = set()
    for tx in transactions or []:
        amount = float(tx.get("amount", 0) or 0)
        if amount >= 0:
            continue
        category = str(tx.get("category") or "general").strip().lower()
        raw[category] = raw.get(category, 0.0) + abs(amount)
        d = str(tx.get("date") or "")
        if d:
            dates.add(d)

    days_observed = max(30, len(dates)) if dates else 30
    return {cat: round((total / days_observed) * 30.5, 2) for cat, total in raw.items()}


@router.post("/goal")
async def goal_forecast(request: GoalForecastRequest, user_id: str = Depends(resolve_user_id)):
    try:
        target_dt = datetime.strptime(request.target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="target_date must be YYYY-MM-DD")

    today = date.today()
    days_remaining = max(1, (target_dt - today).days)

    transactions = request.ephemeral_transactions or []
    if not transactions:
        tx_data = await forward(
            "GET",
            f"{DATA_SERVICE_URL}/api/transactions/list",
            params={"user_id": user_id},
        )
        transactions = tx_data.get("items", [])

    base_forecast = await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": min(days_remaining, 365)},
    )

    forecast_rows = base_forecast.get("forecast_data", [])
    current_projected_balance = 0.0
    if forecast_rows:
        last = forecast_rows[-1]
        current_projected_balance = float(
            last.get("predicted_balance", last.get("balance", 0.0)) or 0.0
        )

    delta = round(max(0.0, request.target_amount - current_projected_balance), 2)
    required_monthly_savings = round(delta / (days_remaining / 30.5), 2) if delta > 0 else 0.0
    required_daily_savings = round(delta / days_remaining, 2) if delta > 0 else 0.0

    category_spending = _aggregate_category_spending(transactions)

    _essential = frozenset({
        "rent", "mortgage", "emi", "loan", "insurance", "utilities",
        "salary", "income", "paycheck", "tax", "medical", "healthcare", "education",
    })
    total_discretionary_spend = sum(
        v for k, v in category_spending.items() if k.lower() not in _essential
    )
    is_achievable = delta <= 0 or required_monthly_savings <= (total_discretionary_spend * 0.5)

    cuts_data = await forward(
        "POST",
        f"{AI_SERVICE_URL}/api/ai/goal-cuts",
        json={
            "category_spending": category_spending,
            "required_monthly_savings": required_monthly_savings,
            "days_remaining": days_remaining,
            "language": request.language,
            "is_achievable": is_achievable,
        },
    )
    suggested_cuts = cuts_data.get("suggested_cuts", [])

    return {
        "goal": {
            "target_amount": round(float(request.target_amount), 2),
            "target_date": request.target_date,
            "days_remaining": days_remaining,
            "current_projected_balance": round(current_projected_balance, 2),
            "delta": delta,
            "required_monthly_savings": required_monthly_savings,
            "required_daily_savings": required_daily_savings,
            "is_achievable": is_achievable,
            "category_spending": category_spending,
        },
        "suggested_cuts": suggested_cuts,
        "language": request.language,
    }


@router.get("/history")
async def get_forecast_history(limit: int = 10, user_id: str = Depends(resolve_user_id)):
    transactions = await _fetch_transactions(user_id)
    return await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/history",
        json={"transactions": transactions, "limit": limit},
    )
