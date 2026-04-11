"""Smoke tests for the AI Service."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ai-service"))


def test_ai_service_imports():
    """Verify the AI service module can be loaded."""
    import main as ai_main

    assert hasattr(ai_main, "app")
    assert hasattr(ai_main, "extract_scenario_intent")


def test_extract_intent_spend():
    """A flight purchase should be classified as 'spend'."""
    from main import extract_scenario_intent

    result = extract_scenario_intent("$500 flight to Paris")
    assert result["intent"] == "spend"
    assert result["amount"] == 500.0


def test_extract_intent_save():
    """Skipping purchases should be classified as 'save'."""
    from main import extract_scenario_intent

    result = extract_scenario_intent("Skip coffee for 2 weeks")
    assert result["intent"] == "save"


def test_extract_intent_delay():
    """Late payments should be classified as 'delay'."""
    from main import extract_scenario_intent

    result = extract_scenario_intent("Payday 3 days late")
    assert result["intent"] == "delay"


def test_fallback_explanation_english():
    """Fallback explanation should work without an LLM."""
    from main import _fallback_explanation

    forecast = {
        "forecast_data": [
            {"date": "2024-04-01", "balance": 3000},
            {"date": "2024-04-10", "balance": 2000},
        ],
        "confidence": 78,
    }

    text = _fallback_explanation(forecast, "en")
    assert "2000" in text
    assert "78" in text
