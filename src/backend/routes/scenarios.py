"""
Scenario proxy routes — orchestrates data-service + forecast-service + ai-service.
All routes are protected (JWT required).
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from client import forward
from deps import resolve_user_id

DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")
FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8001")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8002")

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


class ScenarioRequest(BaseModel):
    description: str
    language: str = "en"
    ephemeral_transactions: Optional[List[Dict[str, Any]]] = None


def _infer_daily_spend(transactions: List[Dict[str, Any]]) -> float:
    if not transactions:
        return 60.0

    daily_totals: Dict[str, float] = {}
    for tx in transactions:
        date = str(tx.get("date") or "")
        amount = float(tx.get("amount", 0) or 0)
        if not date or amount >= 0:
            continue
        daily_totals[date] = daily_totals.get(date, 0.0) + abs(amount)

    if not daily_totals:
        return 60.0

    values = sorted(daily_totals.values())
    midpoint = len(values) // 2
    if len(values) % 2 == 1:
        median = values[midpoint]
    else:
        median = (values[midpoint - 1] + values[midpoint]) / 2
    return max(20.0, min(250.0, median))


def _build_transaction_context(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    inflow = 0.0
    outflow = 0.0
    for tx in transactions or []:
        amount = float(tx.get("amount", 0) or 0)
        if amount >= 0:
            inflow += amount
        else:
            outflow += abs(amount)

    return {
        "transaction_count": len(transactions or []),
        "median_daily_spend": round(_infer_daily_spend(transactions), 2),
        "total_inflow": round(inflow, 2),
        "total_outflow": round(outflow, 2),
    }


def _extract_duration_days(text: str) -> Optional[int]:
    if not text:
        return None

    days_match = re.search(r"for\s+(\d{1,3})\s+days?", text)
    if days_match:
        return max(1, int(days_match.group(1)))

    weeks_match = re.search(r"for\s+(\d{1,2})\s+weeks?", text)
    if weeks_match:
        return max(1, int(weeks_match.group(1)) * 7)

    return None


def _extract_daily_amount_hint(text: str) -> Optional[float]:
    if not text:
        return None

    patterns = [
        r"(?:\$|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:/|per)\s*day",
        r"(?:\$|₹)?\s*([0-9]+(?:\.[0-9]+)?)\s*a\s*day",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return max(0.0, float(match.group(1)))

    return None


def _looks_like_spend_reduction(text: str) -> bool:
    if not text:
        return False

    reduction_terms = ["don't", "dont", "no", "skip", "avoid", "cut", "reduce", "stop"]
    spend_terms = [
        "shop",
        "shopping",
        "spend",
        "coffee",
        "food",
        "dining",
        "eating out",
        "entertainment",
        "subscription",
    ]
    return any(term in text for term in reduction_terms) and any(term in text for term in spend_terms)


def _estimate_daily_reduction(transactions: List[Dict[str, Any]], text: str) -> float:
    daily_spend = _infer_daily_spend(transactions)
    text = text or ""

    # Apply category-like multipliers so targeted scenarios (coffee/subscriptions)
    # impact less than broad "no shopping" requests.
    multiplier = 0.30
    if any(k in text for k in ["coffee", "tea", "cafe"]):
        multiplier = 0.10
    elif any(k in text for k in ["subscription", "netflix", "spotify", "prime"]):
        multiplier = 0.12
    elif any(k in text for k in ["food", "dining", "restaurant", "swiggy", "zomato", "ubereats"]):
        multiplier = 0.20
    elif any(k in text for k in ["shopping", "shop", "mall", "amazon", "flipkart"]):
        multiplier = 0.35

    hinted = _extract_daily_amount_hint(text)
    if hinted and hinted > 0:
        return max(5.0, min(200.0, hinted))

    return max(8.0, min(150.0, round(daily_spend * multiplier, 2)))


def _enhance_scenario_events(events: List[Dict[str, Any]], description: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert spend-reduction intents into duration-limited recurring savings events."""
    text = (description or "").lower()
    if not _looks_like_spend_reduction(text):
        return events

    duration_days = _extract_duration_days(text) or 14
    daily_savings = _estimate_daily_reduction(transactions, text)
    monthly_equivalent = round(daily_savings * 30.5, 2)

    transformed: List[Dict[str, Any]] = []
    transformed_any = False

    for event in events:
        if not isinstance(event, dict):
            continue

        event_text = str(event.get("description") or description or "").lower()
        should_transform = _looks_like_spend_reduction(event_text) or len(events) == 1

        if not should_transform:
            transformed.append(event)
            continue

        transformed_any = True
        transformed.append(
            {
                "type": "recurring_income",
                "amount": monthly_equivalent,
                "date_offset_days": max(int(event.get("date_offset_days", 0) or 0), 0),
                "duration_days": duration_days,
                "description": event.get("description") or description,
            }
        )

    if transformed_any:
        return transformed

    # If parser missed the event entirely, synthesize one from the free-form text.
    return [
        {
            "type": "recurring_income",
            "amount": monthly_equivalent,
            "date_offset_days": 0,
            "duration_days": duration_days,
            "description": description,
        }
    ]


@router.post("/analyze")
async def analyze_scenario(request: ScenarioRequest, user_id: str = Depends(resolve_user_id)):
    # 1. Fetch transactions
    if request.ephemeral_transactions:
        transactions = request.ephemeral_transactions
    else:
        tx_data = await forward(
            "GET",
            f"{DATA_SERVICE_URL}/api/transactions/list",
            params={"user_id": user_id},
        )
        transactions = tx_data.get("transactions") or tx_data.get("items", [])

    # 2. Generate base forecast
    base_forecast = await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": 42},
    )

    # 3. Extract intent from user description
    intent = await forward(
        "POST",
        f"{AI_SERVICE_URL}/api/ai/extract-intent",
        json={
            "user_input": request.description,
            "language": request.language,
            "transaction_context": _build_transaction_context(transactions),
        },
    )

    # 4. Run scenario on the base forecast
    parsed_events = intent.get("events") if isinstance(intent, dict) else None
    if not isinstance(parsed_events, list) or not parsed_events:
        # Backward-compatible fallback for older AI parser shape.
        parsed_events = [
            {
                "type": "one_time_income" if intent.get("intent") in {"income", "save"} else "one_time_spend",
                "amount": float(intent.get("amount", 0.0) or 0.0),
                "date_offset_days": 0,
                "description": request.description,
            }
        ]

    parsed_events = _enhance_scenario_events(parsed_events, request.description, transactions)

    scenario_results = await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/scenario",
        json={
            "base_forecast": base_forecast,
            "scenario_events": parsed_events,
        },
    )

    # 5. Generate narrative explanation
    explanation = await forward(
        "POST",
        f"{AI_SERVICE_URL}/api/ai/scenario-explanation",
        json={
            "scenario_results": scenario_results,
            "original_forecast": base_forecast,
            "language": request.language,
        },
    )

    return {
        **scenario_results,
        "explanation": explanation.get("explanation", ""),
        "intent": intent,
    }


@router.get("/suggestions")
async def get_scenario_suggestions(language: str = "en", user_id: str = Depends(resolve_user_id)):
    return await forward("GET", f"{AI_SERVICE_URL}/api/ai/suggestions", params={"language": language})
