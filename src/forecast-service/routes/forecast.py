"""
Forecast HTTP endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from schemas.requests import ForecastGenerateRequest, ForecastHistoryRequest, ScenarioRunRequest
from services.forecast_service import extract_alerts, generate_forecast, run_scenario

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.post("/generate")
async def api_generate_forecast(request: ForecastGenerateRequest):
    """Generate a 6-week balance forecast."""
    result = generate_forecast(request.transactions, request.days, request.starting_balance)
    result["alerts"] = extract_alerts(result)
    return result


@router.post("/history")
async def api_forecast_history(request: ForecastHistoryRequest):
    """Return multiple short-horizon forecasts for the history view."""
    items = [generate_forecast(request.transactions, 14) for _ in range(min(request.limit, 3))]
    return {"items": items}


@router.post("/scenario")
async def api_run_scenario(request: ScenarioRunRequest):
    """Run a what-if scenario on a base forecast."""
    low, likely, high = run_scenario(request.base_forecast, request.scenario)
    return {"low": low, "likely": likely, "high": high}
