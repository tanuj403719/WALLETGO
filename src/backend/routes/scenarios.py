"""
Scenario proxy routes — orchestrates data-service + forecast-service + ai-service.
All routes are protected (JWT required).
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
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


class SaveScenarioRequest(BaseModel):
    title: Optional[str] = None
    description: str
    language: str = "en"
    analysis: Optional[Dict[str, Any]] = None
    low: Optional[Dict[str, Any]] = None
    likely: Optional[Dict[str, Any]] = None
    high: Optional[Dict[str, Any]] = None
    explanation: str = ""
    intent: Optional[Dict[str, Any]] = None


class TargetBalanceRequest(BaseModel):
    target_balance: float
    horizon_days: int = 90
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


def _normalize_category(value: str) -> str:
    key = " ".join(str(value or "general").strip().lower().split())
    if not key:
        return "general"

    aliases = {
        "restaurant": "food",
        "dining": "food",
        "takeout": "food",
        "coffee": "food",
        "salary": "income",
        "paycheck": "income",
        "shopping": "shopping",
        "groceries": "groceries",
        "grocery": "groceries",
        "subscriptions": "subscriptions",
        "bills": "bills",
    }
    return aliases.get(key, key)


def _category_cut_cap(category: str) -> float:
    caps = {
        "food": 0.35,
        "shopping": 0.35,
        "entertainment": 0.35,
        "subscriptions": 0.50,
        "groceries": 0.15,
        "transport": 0.20,
        "bills": 0.10,
        "rent": 0.05,
        "emi": 0.05,
        "insurance": 0.05,
    }
    return caps.get(category, 0.20)


def _build_target_balance_plan(
    transactions: List[Dict[str, Any]],
    target_balance: float,
    horizon_days: int,
    projected_balance: float,
) -> Dict[str, Any]:
    safe_horizon = max(7, min(horizon_days, 365))
    target_gap = round(max(0.0, float(target_balance) - float(projected_balance)), 2)
    monthly_required = round(target_gap / (safe_horizon / 30.5), 2) if target_gap > 0 else 0.0

    expense_by_category: Dict[str, float] = {}
    for tx in transactions or []:
        amount = float(tx.get("amount", 0) or 0)
        if amount >= 0:
            continue
        category = _normalize_category(str(tx.get("category") or "general"))
        expense_by_category[category] = expense_by_category.get(category, 0.0) + abs(amount)

    if transactions:
        dates = [str(tx.get("date") or "") for tx in transactions if tx.get("date")]
        days_observed = max(30, len(set(dates))) if dates else 30
    else:
        days_observed = 30

    category_monthly: List[Dict[str, Any]] = []
    for category, total in expense_by_category.items():
        monthly_spend = (total / days_observed) * 30.5
        max_cut = monthly_spend * _category_cut_cap(category)
        category_monthly.append(
            {
                "category": category,
                "monthly_spend": round(monthly_spend, 2),
                "max_recommended_cut": round(max_cut, 2),
            }
        )
    category_monthly.sort(key=lambda item: item.get("max_recommended_cut", 0.0), reverse=True)

    remaining = monthly_required
    recommendations: List[Dict[str, Any]] = []
    for item in category_monthly:
        if remaining <= 0:
            break
        proposed = min(item["max_recommended_cut"], remaining)
        if proposed <= 0:
            continue
        monthly_spend = max(item["monthly_spend"], 1.0)
        cut_percent = min(80.0, (proposed / monthly_spend) * 100.0)
        recommendations.append(
            {
                "category": item["category"],
                "recommended_cut_monthly": round(proposed, 2),
                "recommended_cut_daily": round(proposed / 30.5, 2),
                "cut_percent": round(cut_percent, 1),
            }
        )
        remaining = round(max(0.0, remaining - proposed), 2)

    achievable = target_gap <= 0 or remaining <= 0
    return {
        "target_balance": round(float(target_balance), 2),
        "horizon_days": safe_horizon,
        "projected_balance_without_changes": round(float(projected_balance), 2),
        "target_gap": target_gap,
        "required_monthly_savings": monthly_required,
        "recommended_cuts": recommendations,
        "is_target_achievable_with_recommended_cuts": achievable,
        "uncovered_monthly_gap": remaining,
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


@router.post("/save")
async def save_scenario(request: SaveScenarioRequest, user_id: str = Depends(resolve_user_id)):
    analysis = request.analysis or {}
    low = request.low or analysis.get("low")
    likely = request.likely or analysis.get("likely")
    high = request.high or analysis.get("high")
    explanation = request.explanation or analysis.get("explanation", "")
    intent = request.intent or analysis.get("intent")

    intent_description = ""
    if isinstance(intent, dict):
        intent_description = str(intent.get("description") or "").strip()
    resolved_description = intent_description or str(request.description or "").strip() or "What-if scenario"

    if not isinstance(low, dict) or not isinstance(likely, dict) or not isinstance(high, dict):
        raise HTTPException(
            status_code=400,
            detail="Provide scenario payload via analysis or low/likely/high objects.",
        )

    return await forward(
        "POST",
        f"{DATA_SERVICE_URL}/api/scenarios/save",
        json={
            "user_id": user_id,
            "title": request.title,
            "description": resolved_description,
            "language": request.language,
            "low_result": low,
            "likely_result": likely,
            "high_result": high,
            "explanation": explanation,
            "intent": intent,
        },
    )


@router.get("/saved")
async def list_saved_scenarios(
    limit: int = 10,
    user_id: str = Depends(resolve_user_id),
):
    return await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/scenarios/saved",
        params={"user_id": user_id, "limit": limit},
    )


@router.get("/saved/{scenario_id}")
async def get_saved_scenario(scenario_id: str, user_id: str = Depends(resolve_user_id)):
    return await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/scenarios/saved/{scenario_id}",
        params={"user_id": user_id},
    )


@router.get("/compare")
async def compare_saved_scenarios(
    left_id: str,
    right_id: str,
    user_id: str = Depends(resolve_user_id),
):
    return await forward(
        "GET",
        f"{DATA_SERVICE_URL}/api/scenarios/compare",
        params={"user_id": user_id, "left_id": left_id, "right_id": right_id},
    )


@router.post("/target-balance")
async def plan_target_balance(request: TargetBalanceRequest, user_id: str = Depends(resolve_user_id)):
    safe_horizon = max(7, min(request.horizon_days, 365))

    if request.ephemeral_transactions:
        transactions = request.ephemeral_transactions
    else:
        tx_data = await forward(
            "GET",
            f"{DATA_SERVICE_URL}/api/transactions/list",
            params={"user_id": user_id},
        )
        transactions = tx_data.get("transactions") or tx_data.get("items", [])

    base_forecast = await forward(
        "POST",
        f"{FORECAST_SERVICE_URL}/api/forecast/generate",
        json={"transactions": transactions, "days": safe_horizon},
    )
    forecast_rows = base_forecast.get("forecast_data", [])
    projected_balance = 0.0
    if forecast_rows:
        last = forecast_rows[-1]
        projected_balance = float(last.get("predicted_balance", last.get("balance", 0.0)) or 0.0)

    plan = _build_target_balance_plan(
        transactions=transactions,
        target_balance=request.target_balance,
        horizon_days=safe_horizon,
        projected_balance=projected_balance,
    )

    advice = await forward(
        "POST",
        f"{AI_SERVICE_URL}/api/ai/target-balance-advice",
        json={
            "target_plan": plan,
            "language": request.language,
            "transaction_context": _build_transaction_context(transactions),
        },
    )

    return {
        "target_plan": plan,
        "advice": advice.get("advice", ""),
        "language": request.language,
    }


@router.get("/suggestions")
async def get_scenario_suggestions(language: str = "en", user_id: str = Depends(resolve_user_id)):
    return await forward("GET", f"{AI_SERVICE_URL}/api/ai/suggestions", params={"language": language})
