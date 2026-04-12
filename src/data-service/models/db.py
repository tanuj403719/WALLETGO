"""
SQLAlchemy models and database session for the data-service.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = os.getenv("DATABASE_PATH", "walletgo.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    language_preference = Column(String, nullable=False, default="en")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    date = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
