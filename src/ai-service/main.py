"""
WALLETGO AI Service
===================
LLM-powered financial explanation microservice.
All domain logic lives in services/; all HTTP handlers live in routes/.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from routes.ai import router as ai_router
from services.ai_service import is_llm_available

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="WALLETGO AI Service",
    description="LLM-powered financial explanation microservice.",
    version="1.0.0",
)

app.include_router(ai_router)


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "WALLETGO AI Service",
        "llm_available": is_llm_available(),
    }
