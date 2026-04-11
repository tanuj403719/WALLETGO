"""Transaction endpoints."""

from typing import Dict, List

from fastapi import APIRouter

from app.services.natwest_service import NatWestService

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
natwest_service = NatWestService()

@router.get("/list")
async def list_transactions(limit: int = 100, offset: int = 0):
    """List user's transactions."""

    transactions = natwest_service.get_demo_transactions()
    return {"items": transactions[offset : offset + limit], "count": len(transactions)}

@router.get("/recurring")
async def get_recurring_bills():
    """Get identified recurring bills."""

    return {
        "items": [
            {"type": "income", "amount": 4000, "frequency": "monthly", "day_of_month": 5, "category": "salary"},
            {"type": "expense", "amount": 1500, "frequency": "monthly", "day_of_month": 1, "category": "rent"},
            {"type": "expense", "amount": 15, "frequency": "monthly", "day_of_month": 10, "category": "netflix"},
        ]
    }

@router.get("/stats")
async def get_transaction_stats():
    """Get transaction statistics."""

    transactions = natwest_service.get_demo_transactions()
    income = sum(item["amount"] for item in transactions if item["amount"] > 0)
    expense = abs(sum(item["amount"] for item in transactions if item["amount"] < 0))
    return {"income": income, "expense": expense, "net": income - expense, "count": len(transactions)}
