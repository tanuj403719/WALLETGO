"""
Transaction endpoints: list, stats, recurring.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import UploadFile, File, HTTPException

from models.db import SessionLocal, TransactionModel
from services.auth_service import DEMO_USER_ID
from services.statement_parser import parse_statement, StatementParseError
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


@router.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    """Parse an uploaded bank statement and replace stored transactions."""
    filename = file.filename or ""
    if not (filename.lower().endswith(".csv") or filename.lower().endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only .csv and .pdf files are supported")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

    try:
        transactions = parse_statement(content, filename)
    except StatementParseError as e:
        raise HTTPException(
            status_code=422,
            detail={"message": str(e), "detected_headers": e.detected_headers},
        )

    with SessionLocal() as session:
        session.query(TransactionModel).filter_by(user_id=DEMO_USER_ID).delete()
        for tx in transactions:
            it = TransactionModel(
                user_id=DEMO_USER_ID,
                date=tx["date"],
                amount=tx["amount"],
                description=tx["description"],
                category=tx["category"],
            )
            session.add(it)
        session.commit()

    return {"imported": len(transactions), "preview": transactions[:3]}
