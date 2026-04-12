"""
Authentication business logic: password hashing, JWT issuance, and database seeding.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import bcrypt
import jwt

from models.db import SessionLocal, TransactionModel, UserModel

logger = logging.getLogger("walletgo.data.auth")

JWT_SECRET = os.getenv("JWT_SECRET", "walletgo-hackathon-demo-secret-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

DEMO_USER_ID = "demo-user-00000000"

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


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "aud": "authenticated",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def seed_database() -> None:
    """Populate the database with demo data if it is empty."""
    with SessionLocal() as session:
        if session.query(TransactionModel).first() is not None:
            return  # Already seeded

        logger.info("Seeding database with demo transactions…")

        demo_user = UserModel(
            id=DEMO_USER_ID,
            email="demo@radar.com",
            password_hash=hash_password("demo123"),
            display_name="Demo User",
        )
        session.merge(demo_user)

        for tx in SEED_TRANSACTIONS:
            session.add(
                TransactionModel(
                    user_id=DEMO_USER_ID,
                    date=tx["date"],
                    amount=tx["amount"],
                    category=tx["category"],
                    description=tx["description"],
                )
            )

        session.commit()
        logger.info("Seeded %d transactions for demo user.", len(SEED_TRANSACTIONS))
