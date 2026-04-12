"""
Transaction proxy routes — forwards to data-service.
All routes are protected (JWT required).
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from client import forward, get_client
from deps import verify_token

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/parse-only")
async def parse_statement_only(file: UploadFile = File(...)):
    """Parse statement and return transactions without persistence (demo flow)."""
    content = await file.read()
    client = get_client()
    response = await client.post(
        f"{DATA_SERVICE_URL}/api/transactions/parse-only",
        files={"file": (file.filename, content, file.content_type)},
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()


@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_token),
    replace_existing: bool = False,
):
    """Proxy a bank statement upload to the data-service."""
    content = await file.read()
    client = get_client()
    response = await client.post(
        f"{DATA_SERVICE_URL}/api/transactions/upload",
        params={"user_id": user_id, "replace_existing": replace_existing},
        files={"file": (file.filename, content, file.content_type)},
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()


@router.get("/list")
async def list_transactions(
    limit: int = 100, offset: int = 0, user_id: str = Depends(verify_token)
):
    return await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/transactions/list",
        params={"limit": limit, "offset": offset, "user_id": user_id},
    )


@router.get("/recurring")
async def get_recurring_bills(user_id: str = Depends(verify_token)):
    return await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/transactions/recurring",
        params={"user_id": user_id},
    )


@router.get("/stats")
async def get_transaction_stats(user_id: str = Depends(verify_token)):
    return await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/transactions/stats",
        params={"user_id": user_id},
    )
