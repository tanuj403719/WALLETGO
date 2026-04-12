"""
Transaction endpoints: list, stats, recurring.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Query
from fastapi import UploadFile, File, HTTPException

from services.auth_service import DEMO_USER_ID
from services.statement_parser import parse_statement, StatementParseError
from services.transaction_service import (
    clear_transactions,
    get_recurring_bills,
    get_stats,
    get_transaction_fingerprints,
    get_transactions,
    insert_transactions,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _transaction_fingerprint(date: str, amount: float, description: str) -> str:
    normalized_description = " ".join((description or "").strip().lower().split())
    payload = f"{date}|{float(amount):.2f}|{normalized_description}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@router.post("/parse-only")
async def parse_only_statement(file: UploadFile = File(...)):
    """Parse an uploaded statement and return transactions without persistence."""
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

    return transactions


@router.get("/list")
async def list_transactions(
    limit: int = 100,
    offset: int = 0,
    user_id: str = Query(default=DEMO_USER_ID),
):
    return get_transactions(user_id=user_id, limit=limit, offset=offset)


@router.get("/stats")
async def transaction_stats(user_id: str = Query(default=DEMO_USER_ID)):
    return get_stats(user_id=user_id)


@router.get("/recurring")
async def recurring_bills(user_id: str = Query(default=DEMO_USER_ID)):
    return get_recurring_bills(user_id=user_id)


@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    user_id: str = Query(..., min_length=1),
    replace_existing: bool = Query(default=False),
):
    """Parse an uploaded bank statement and merge net-new transactions for the user."""
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

    replaced_count = 0
    if replace_existing:
        replaced_count = len(get_transaction_fingerprints(user_id))
        clear_transactions(user_id)
        existing_fingerprints = set()
    else:
        existing_fingerprints = get_transaction_fingerprints(user_id)

    pending_rows = []
    preview = []
    for tx in transactions:
        fingerprint = _transaction_fingerprint(tx["date"], tx["amount"], tx["description"])
        if fingerprint in existing_fingerprints:
            continue

        pending_rows.append({**tx, "fingerprint": fingerprint})
        existing_fingerprints.add(fingerprint)
        if len(preview) < 3:
            preview.append(tx)

    imported = insert_transactions(user_id=user_id, transactions=pending_rows)

    return {
        "parsed_total": len(transactions),
        "imported": imported,
        "skipped_duplicates": len(transactions) - imported,
        "replaced_existing": replace_existing,
        "replaced_count": replaced_count,
        "preview": preview,
    }
