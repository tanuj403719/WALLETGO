"""
Transaction query logic: listing, stats, and recurring bill detection from real data.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
import hashlib
from typing import Any, Dict, List

from services.auth_service import DEMO_USER_ID
from services.supabase_service import TRANSACTIONS_TABLE, get_supabase_client

logger = logging.getLogger("walletgo.data.transactions")


def get_transactions(user_id: str = DEMO_USER_ID, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    client = get_supabase_client()
    safe_limit = max(1, min(limit, 1000))
    safe_offset = max(0, offset)

    response = (
        client.table(TRANSACTIONS_TABLE)
        .select("date,amount,category,description", count="exact")
        .eq("user_id", user_id)
        .order("date")
        .range(safe_offset, safe_offset + safe_limit - 1)
        .execute()
    )

    rows = response.data or []
    items = [
        {
            "date": row.get("date"),
            "amount": float(row.get("amount", 0) or 0),
            "category": row.get("category") or "general",
            "description": row.get("description") or "",
        }
        for row in rows
    ]
    total = response.count if response.count is not None else len(items)
    return {"items": items, "transactions": items, "count": total}


def get_stats(user_id: str = DEMO_USER_ID) -> Dict[str, Any]:
    client = get_supabase_client()
    response = (
        client.table(TRANSACTIONS_TABLE)
        .select("amount")
        .eq("user_id", user_id)
        .execute()
    )
    rows = response.data or []

    income = sum(float(r.get("amount", 0) or 0) for r in rows if float(r.get("amount", 0) or 0) > 0)
    expense = abs(sum(float(r.get("amount", 0) or 0) for r in rows if float(r.get("amount", 0) or 0) < 0))
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net": round(income - expense, 2),
        "count": len(rows),
    }


def get_recurring_bills(user_id: str = DEMO_USER_ID) -> Dict[str, Any]:
    """
    Detect recurring transactions from actual data.

    A transaction is considered recurring if the same description appears
    multiple times with amounts that are consistent (within 10%) and dates
    that are spaced roughly 25–35 days apart (monthly cadence).
    """
    client = get_supabase_client()
    response = (
        client.table(TRANSACTIONS_TABLE)
        .select("date,amount,description,category")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )
    rows = response.data or []

    # Group by (description, sign) so "Salary" and "Rent" don't merge
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        description = str(row.get("description") or "")
        key = description.strip().lower()
        groups[key].append(
            {
                "date": row.get("date"),
                "amount": float(row.get("amount", 0) or 0),
                "description": description,
                "category": row.get("category") or "general",
            }
        )

    recurring = []
    for desc, entries in groups.items():
        if len(entries) < 2:
            continue

        amounts = [abs(e["amount"]) for e in entries]
        avg_amount = sum(amounts) / len(amounts)

        # All amounts within 10% of the average → consistent
        if any(abs(a - avg_amount) / (avg_amount or 1) > 0.10 for a in amounts):
            continue

        # Check date spacing
        try:
            dates = sorted(datetime.strptime(e["date"], "%Y-%m-%d") for e in entries)
        except ValueError:
            continue

        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_gap = sum(gaps) / len(gaps)

        if 25 <= avg_gap <= 35:
            frequency = "monthly"
            day_of_month = dates[0].day
        elif 6 <= avg_gap <= 8:
            frequency = "weekly"
            day_of_month = None
        else:
            continue

        tx_type = "income" if entries[0]["amount"] > 0 else "expense"
        item: Dict[str, Any] = {
            "description": entries[0]["description"],
            "type": tx_type,
            "amount": round(avg_amount, 2),
            "frequency": frequency,
            "category": entries[0]["category"],
        }
        if day_of_month is not None:
            item["day_of_month"] = day_of_month

        recurring.append(item)

    return {"items": recurring, "recurring": recurring}


def _transaction_fingerprint(date: str, amount: float, description: str) -> str:
    normalized_description = " ".join((description or "").strip().lower().split())
    payload = f"{date}|{float(amount):.2f}|{normalized_description}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_transaction_fingerprints(user_id: str) -> set[str]:
    client = get_supabase_client()
    response = (
        client.table(TRANSACTIONS_TABLE)
        .select("fingerprint")
        .eq("user_id", user_id)
        .execute()
    )
    rows = response.data or []
    return {str(row.get("fingerprint")) for row in rows if row.get("fingerprint")}


def insert_transactions(user_id: str, transactions: List[Dict[str, Any]]) -> int:
    if not transactions:
        return 0

    payload = []
    for tx in transactions:
        date = tx.get("date")
        amount = float(tx.get("amount", 0) or 0)
        description = tx.get("description") or ""
        payload.append(
            {
                "user_id": user_id,
                "date": date,
                "amount": amount,
                "category": tx.get("category") or "general",
                "description": description,
                "fingerprint": tx.get("fingerprint") or _transaction_fingerprint(date, amount, description),
            }
        )

    client = get_supabase_client()
    client.table(TRANSACTIONS_TABLE).insert(payload).execute()
    return len(payload)
