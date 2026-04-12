"""
Demo constants and Supabase seed helpers.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Dict, List

from services.supabase_service import TRANSACTIONS_TABLE, get_supabase_client

logger = logging.getLogger("walletgo.data.auth")

DEMO_USER_ID = "demo-user"

SEED_TRANSACTIONS: List[Dict] = [
    {"date": "2024-03-01", "amount": -1500.00, "category": "rent", "description": "Rent"},
    {"date": "2024-03-02", "amount": -45.00, "category": "utilities", "description": "Electric bill"},
    {"date": "2024-03-05", "amount": 4000.00, "category": "income", "description": "Salary"},
    {"date": "2024-03-07", "amount": -22.50, "category": "transport", "description": "Oyster top-up"},
    {"date": "2024-03-08", "amount": -85.00, "category": "groceries", "description": "Weekly shopping"},
    {"date": "2024-03-10", "amount": -15.00, "category": "subscription", "description": "Netflix"},
    {"date": "2024-03-11", "amount": -9.99, "category": "subscription", "description": "Spotify"},
    {"date": "2024-03-12", "amount": -35.00, "category": "dining", "description": "Lunch with team"},
    {"date": "2024-03-14", "amount": -60.00, "category": "shopping", "description": "Amazon order"},
    {"date": "2024-03-15", "amount": -120.00, "category": "dining", "description": "Restaurant dinner"},
    {"date": "2024-03-17", "amount": -90.00, "category": "groceries", "description": "Weekly shopping"},
    {"date": "2024-03-19", "amount": 250.00, "category": "income", "description": "Freelance payment"},
    {"date": "2024-03-20", "amount": -50.00, "category": "transport", "description": "Uber rides"},
    {"date": "2024-03-22", "amount": -30.00, "category": "health", "description": "Pharmacy"},
    {"date": "2024-03-24", "amount": -75.00, "category": "groceries", "description": "Weekly shopping"},
    {"date": "2024-03-25", "amount": -200.00, "category": "shopping", "description": "Clothing"},
    {"date": "2024-03-28", "amount": -18.00, "category": "entertainment", "description": "Cinema tickets"},
    {"date": "2024-03-30", "amount": -42.00, "category": "dining", "description": "Takeaway"},
]


def _transaction_fingerprint(date: str, amount: float, description: str) -> str:
    normalized_description = " ".join((description or "").strip().lower().split())
    payload = f"{date}|{float(amount):.2f}|{normalized_description}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seed_demo_transactions() -> None:
    """Populate Supabase with demo transactions if missing."""
    client = get_supabase_client()

    existing_response = (
        client.table(TRANSACTIONS_TABLE)
        .select("fingerprint")
        .eq("user_id", DEMO_USER_ID)
        .execute()
    )
    existing_fingerprints = {
        str(row.get("fingerprint"))
        for row in (existing_response.data or [])
        if row.get("fingerprint")
    }

    payload = []
    for tx in SEED_TRANSACTIONS:
        fingerprint = _transaction_fingerprint(tx["date"], tx["amount"], tx["description"])
        if fingerprint in existing_fingerprints:
            continue
        payload.append(
            {
                "user_id": DEMO_USER_ID,
                "date": tx["date"],
                "amount": tx["amount"],
                "category": tx["category"],
                "description": tx["description"],
                "fingerprint": fingerprint,
            }
        )
        existing_fingerprints.add(fingerprint)

    if not payload:
        return

    client.table(TRANSACTIONS_TABLE).insert(payload).execute()
    logger.info("Seeded %d transactions for demo user.", len(payload))
