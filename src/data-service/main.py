"""
WALLETGO Data Service
=====================
Handles user authentication and transaction persistence using SQLite.
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

from models.db import Base, DB_PATH, engine
from routes.auth import router as auth_router
from routes.transactions import router as transactions_router
from services.auth_service import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("walletgo.data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_database()
    logger.info("Data service ready — SQLite at %s", DB_PATH)
    yield


app = FastAPI(
    title="WALLETGO Data Service",
    description="Banking data and local persistence microservice (SQLite).",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(transactions_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "WALLETGO Data Service", "database": "sqlite"}
