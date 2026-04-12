"""
WALLETGO Data Service
=====================
Handles transaction persistence using Supabase Postgres.
All domain logic lives in services/; all HTTP handlers live in routes/.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Load .env from project root (2 levels up from src/data-service/)
from pathlib import Path
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

from routes.auth import router as auth_router
from routes.transactions import router as transactions_router
from services.auth_service import SEED_TRANSACTIONS as DEMO_SEED_TRANSACTIONS, seed_demo_transactions
from services.supabase_service import TRANSACTIONS_TABLE, assert_supabase_ready

SEED_TRANSACTIONS = DEMO_SEED_TRANSACTIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("walletgo.data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    assert_supabase_ready()
    seed_demo_transactions()
    logger.info("Data service ready — Supabase table '%s'", TRANSACTIONS_TABLE)
    yield


app = FastAPI(
    title="WALLETGO Data Service",
    description="Banking data persistence microservice (Supabase).",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(transactions_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "WALLETGO Data Service", "database": "supabase"}
