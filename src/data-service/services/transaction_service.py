"""
Transaction query logic: listing, stats, and recurring bill detection from real data.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from models.db import SessionLocal, TransactionModel
from services.auth_service import DEMO_USER_ID

logger = logging.getLogger("walletgo.data.transactions")


def get_transactions(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    with SessionLocal() as session:
        rows = (
            session.query(TransactionModel)
            .filter_by(user_id=DEMO_USER_ID)
            .order_by(TransactionModel.date)
            .offset(offset)
            .limit(limit)
            .all()
        )
        total = session.query(TransactionModel).filter_by(user_id=DEMO_USER_ID).count()

    items = [
        {
            "date": row.date,
            "amount": row.amount,
            "category": row.category,
            "description": row.description,
        }
        for row in rows
    ]
    return {"items": items, "count": total}


def get_stats() -> Dict[str, Any]:
    with SessionLocal() as session:
        rows = (
            session.query(TransactionModel)
            .filter_by(user_id=DEMO_USER_ID)
            .all()
        )

    income = sum(r.amount for r in rows if r.amount > 0)
    expense = abs(sum(r.amount for r in rows if r.amount < 0))
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net": round(income - expense, 2),
        "count": len(rows),
    }


def get_recurring_bills() -> Dict[str, Any]:
    """
    Detect recurring transactions from actual data.

    A transaction is considered recurring if the same description appears
    multiple times with amounts that are consistent (within 10%) and dates
    that are spaced roughly 25–35 days apart (monthly cadence).
    """
    with SessionLocal() as session:
        rows = (
            session.query(TransactionModel)
            .filter_by(user_id=DEMO_USER_ID)
            .order_by(TransactionModel.date)
            .all()
        )

    # Group by (description, sign) so "Salary" and "Rent" don't merge
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        key = row.description.strip().lower()
        groups[key].append({"date": row.date, "amount": row.amount})

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
            "category": rows[
                next(
                    i
                    for i, r in enumerate(rows)
                    if r.description.strip().lower() == desc
                )
            ].category,
        }
        if day_of_month is not None:
            item["day_of_month"] = day_of_month

        recurring.append(item)

    return {"items": recurring}
