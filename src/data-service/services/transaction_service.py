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


def _description_key(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _detect_recurring_patterns(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Infer recurring transaction patterns from cadence + amount consistency."""
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = _description_key(str(row.get("description") or ""))
        if not key:
            continue
        groups[key].append(row)

    recurring: List[Dict[str, Any]] = []
    for key, entries in groups.items():
        if len(entries) < 2:
            continue

        amounts = [abs(float(e.get("amount", 0) or 0)) for e in entries]
        avg_amount = sum(amounts) / len(amounts)
        if avg_amount <= 0:
            continue

        if any(abs(a - avg_amount) / avg_amount > 0.10 for a in amounts):
            continue

        try:
            dates = sorted(datetime.strptime(str(e.get("date")), "%Y-%m-%d") for e in entries)
        except ValueError:
            continue

        if len(dates) < 2:
            continue

        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_gap = sum(gaps) / len(gaps)

        frequency = ""
        day_of_month = None
        day_of_week = None
        if 25 <= avg_gap <= 35:
            frequency = "monthly"
            day_of_month = dates[-1].day
        elif 6 <= avg_gap <= 8:
            frequency = "weekly"
            day_of_week = dates[-1].weekday()
        else:
            continue

        signed_amount = sum(float(e.get("amount", 0) or 0) for e in entries) / len(entries)
        if signed_amount == 0:
            continue

        recurring.append(
            {
                "description_key": key,
                "description": str(entries[-1].get("description") or ""),
                "type": "income" if signed_amount > 0 else "expense",
                "amount": round(abs(signed_amount), 2),
                "signed_amount": round(signed_amount, 2),
                "frequency": frequency,
                "category": str(entries[-1].get("category") or "general"),
                "day_of_month": day_of_month,
                "day_of_week": day_of_week,
            }
        )

    return recurring


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

    recurring_patterns = _detect_recurring_patterns(items)
    recurring_by_key = {pattern["description_key"]: pattern for pattern in recurring_patterns}
    for item in items:
        key = _description_key(str(item.get("description") or ""))
        pattern = recurring_by_key.get(key)
        item["is_recurring"] = bool(pattern)
        if pattern:
            item["recurring_frequency"] = pattern.get("frequency")
            item["recurring_day_of_month"] = pattern.get("day_of_month")
            item["recurring_day_of_week"] = pattern.get("day_of_week")
            item["recurring_signed_amount"] = pattern.get("signed_amount")

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

    normalized_rows = [
        {
            "date": row.get("date"),
            "amount": float(row.get("amount", 0) or 0),
            "description": row.get("description") or "",
            "category": row.get("category") or "general",
        }
        for row in rows
    ]
    recurring = _detect_recurring_patterns(normalized_rows)

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


def clear_transactions(user_id: str) -> None:
    """Delete all transactions for a specific user."""
    client = get_supabase_client()
    client.table(TRANSACTIONS_TABLE).delete().eq("user_id", user_id).execute()
