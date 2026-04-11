"""
Transaction endpoints: list, stats, recurring.
"""

from __future__ import annotations

from fastapi import APIRouter

from services.transaction_service import get_recurring_bills, get_stats, get_transactions

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("/list")
async def list_transactions(limit: int = 100, offset: int = 0):
    return get_transactions(limit=limit, offset=offset)


@router.get("/stats")
async def transaction_stats():
    return get_stats()


@router.get("/recurring")
async def recurring_bills():
    return get_recurring_bills()
