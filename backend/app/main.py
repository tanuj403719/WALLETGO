"""FastAPI application for Liquidity Radar."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.forecast import router as forecast_router
from app.routes.scenarios import router as scenarios_router
from app.routes.transactions import router as transactions_router

load_dotenv()

app = FastAPI(
    title="Liquidity Radar API",
    description="AI-powered financial forecasting API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
    return {"status": "healthy", "service": "Liquidity Radar API"}


@app.get("/api/version")
async def get_version() -> dict:
    return {"version": "0.1.0", "name": "Liquidity Radar API"}