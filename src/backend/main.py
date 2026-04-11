"""
Prism API Gateway
=================
Single entry-point for the React frontend.  Fans out to downstream microservices
via async HTTP.  JWT authentication is enforced here; downstream services trust
the gateway and do not re-verify tokens.

All routes live in routes/; JWT logic lives in deps.py; httpx client in client.py.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from project root (2 levels up from src/backend/)
from pathlib import Path
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

import client as _client_module
from routes.auth import router as auth_router
from routes.forecast import router as forecast_router
from routes.scenarios import router as scenarios_router
from routes.transactions import router as transactions_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prism.gateway")

FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8001")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8002")
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _client_module._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
    logger.info(
        "Gateway started — downstream: forecast=%s, ai=%s, data=%s",
        FORECAST_SERVICE_URL, AI_SERVICE_URL, DATA_SERVICE_URL,
    )
    yield
    await _client_module._client.aclose()
    logger.info("Gateway shutting down — httpx client closed.")


app = FastAPI(
    title="Prism API Gateway",
    description="Single entry-point that fans out to forecast, AI, and data microservices.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(forecast_router)
app.include_router(scenarios_router)
app.include_router(transactions_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "Prism API Gateway"}


@app.get("/api/version")
async def get_version() -> dict:
    return {"version": "1.0.0", "name": "Prism API Gateway"}


@app.get("/api/health/services")
async def service_health() -> dict:
    """Check downstream microservice health."""
    statuses: dict = {}
    for name, url in [
        ("forecast", FORECAST_SERVICE_URL),
        ("ai", AI_SERVICE_URL),
        ("data", DATA_SERVICE_URL),
    ]:
        try:
            resp = await _client_module._client.get(f"{url}/health", timeout=5.0)
            statuses[name] = "healthy" if resp.status_code == 200 else "unhealthy"
        except Exception:
            statuses[name] = "unreachable"
    return {"services": statuses}
