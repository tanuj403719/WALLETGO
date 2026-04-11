"""
Prism Forecast Service
======================
Prophet-based financial forecasting microservice.
All domain logic lives in services/; all HTTP handlers live in routes/.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from routes.forecast import router as forecast_router
from services.forecast_service import Prophet

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Prism Forecast Service",
    description="Prophet-based financial forecasting microservice.",
    version="1.0.0",
)

app.include_router(forecast_router)


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "Prism Forecast Service",
        "model": "prophet" if Prophet is not None else "fallback",
    }
