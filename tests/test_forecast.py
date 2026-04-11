"""Smoke tests for the Forecast Service."""

import sys
import os

# Ensure the forecast-service module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "forecast-service"))


def test_forecast_service_imports():
    """Verify the forecast service module can be loaded."""
    import main as forecast_main

    assert hasattr(forecast_main, "app")
    assert hasattr(forecast_main, "generate_forecast")


def test_generate_forecast_returns_expected_keys():
    """Ensure generate_forecast produces the correct payload shape."""
    from main import generate_forecast

    sample_transactions = [
        {"date": "2024-03-01", "amount": -1500, "category": "rent", "description": "Rent"},
        {"date": "2024-03-05", "amount": 4000, "category": "income", "description": "Salary"},
        {"date": "2024-03-08", "amount": -85, "category": "groceries", "description": "Shopping"},
    ]

    result = generate_forecast(sample_transactions, days=7)

    assert "forecast_data" in result
    assert "confidence" in result
    assert "min_balance" in result
    assert "min_balance_date" in result
    assert "model" in result
    assert len(result["forecast_data"]) == 7


def test_extract_alerts_critical():
    """Alerts should flag negative balances as critical."""
    from main import extract_alerts

    forecast = {
        "forecast_data": [
            {"date": "2024-04-01", "balance": -200},
            {"date": "2024-04-02", "balance": 300},
        ]
    }

    alerts = extract_alerts(forecast)
    assert len(alerts) >= 1
    assert alerts[0]["severity"] == "critical"
