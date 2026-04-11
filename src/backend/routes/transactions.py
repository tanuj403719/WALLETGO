"""
Transaction proxy routes — forwards to data-service.
All routes are protected (JWT required).
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from client import forward
from deps import verify_token

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("/list")
async def list_transactions(
    limit: int = 100, offset: int = 0, user_id: str = Depends(verify_token)
):
    return await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/transactions/list",
        params={"limit": limit, "offset": offset},
    )


@router.get("/recurring")
async def get_recurring_bills(user_id: str = Depends(verify_token)):
    return await forward("GET", f"{DATA_SERVICE_URL}/api/transactions/recurring")


@router.get("/stats")
async def get_transaction_stats(user_id: str = Depends(verify_token)):
    return await forward("GET", f"{DATA_SERVICE_URL}/api/transactions/stats")
