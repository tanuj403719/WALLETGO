"""Smoke tests for the Data Service."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "data-service"))


def test_data_service_imports():
    """Verify the data service module can be loaded."""
    import main as data_main

    assert hasattr(data_main, "app")
    assert hasattr(data_main, "SEED_TRANSACTIONS")


def test_seed_transactions_not_empty():
    """Demo seed data must exist for the hackathon demo."""
    from main import SEED_TRANSACTIONS

    assert len(SEED_TRANSACTIONS) > 0
    assert all("date" in tx for tx in SEED_TRANSACTIONS)
    assert all("amount" in tx for tx in SEED_TRANSACTIONS)
    assert all("category" in tx for tx in SEED_TRANSACTIONS)


def test_seed_has_income_and_expenses():
    """Seed data should contain both income and expense records."""
    from main import SEED_TRANSACTIONS

    has_income = any(tx["amount"] > 0 for tx in SEED_TRANSACTIONS)
    has_expense = any(tx["amount"] < 0 for tx in SEED_TRANSACTIONS)
    assert has_income
    assert has_expense
