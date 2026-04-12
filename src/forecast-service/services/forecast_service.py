"""
Core forecasting logic: hybrid deterministic + stochastic cashflow forecasting.
"""

from __future__ import annotations

import calendar
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from prophet import Prophet
except Exception:  # pragma: no cover
    Prophet = None

logger = logging.getLogger("walletgo.forecast")


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert numeric-ish values to float while guarding against NaN/None."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(parsed):
        return float(default)
    return parsed


def _normalize_description(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _prepare_transactions_frame(transactions: List[Dict]) -> pd.DataFrame:
    """Normalize raw transactions into a clean transaction-level frame."""
    if not transactions:
        return pd.DataFrame(
            {
                "ds": [pd.Timestamp(datetime.utcnow().date())],
                "amount": [0.0],
                "description": [""],
                "category": ["general"],
                "description_key": [""],
            }
        )

    frame = pd.DataFrame(transactions).copy()
    frame["ds"] = pd.to_datetime(frame.get("date"), errors="coerce").dt.normalize()
    frame["amount"] = pd.to_numeric(frame.get("amount"), errors="coerce")
    frame["description"] = frame.get("description", "").astype(str)
    frame["category"] = frame.get("category", "general").fillna("general").astype(str)
    frame = frame.dropna(subset=["ds", "amount"]).sort_values("ds")

    if frame.empty:
        return pd.DataFrame(
            {
                "ds": [pd.Timestamp(datetime.utcnow().date())],
                "amount": [0.0],
                "description": [""],
                "category": ["general"],
                "description_key": [""],
            }
        )

    frame["description_key"] = frame["description"].map(_normalize_description)
    return frame[["ds", "amount", "description", "category", "description_key"]].reset_index(drop=True)


def _daily_flow(frame: pd.DataFrame, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> pd.DataFrame:
    """Aggregate any transaction-level frame into contiguous daily net cashflow."""
    if frame.empty:
        today = pd.Timestamp(datetime.utcnow().date())
        return pd.DataFrame({"ds": [today], "amount": [0.0]})

    grouped = frame.groupby("ds", as_index=False)["amount"].sum().sort_values("ds")
    start_date = pd.Timestamp(start) if start is not None else grouped["ds"].min()
    end_date = pd.Timestamp(end) if end is not None else grouped["ds"].max()
    if end_date < start_date:
        end_date = start_date

    full_range = pd.date_range(start=start_date, end=end_date, freq="D")
    daily = grouped.set_index("ds").reindex(full_range, fill_value=0.0)
    daily.index.name = "ds"
    return daily.reset_index()


def _infer_recurring_patterns(transactions: pd.DataFrame) -> List[Dict]:
    """Infer recurring transactions from cadence + amount consistency."""
    if transactions.empty:
        return []

    recurring_patterns: List[Dict] = []
    grouped = transactions.groupby("description_key", sort=False)

    for description_key, rows in grouped:
        if not description_key or len(rows) < 2:
            continue

        ordered = rows.sort_values("ds")
        amounts = ordered["amount"].astype(float).to_numpy()
        abs_amounts = np.abs(amounts)
        avg_abs_amount = _safe_float(abs_amounts.mean(), 0.0)
        if avg_abs_amount <= 0:
            continue

        variation = np.abs(abs_amounts - avg_abs_amount) / avg_abs_amount
        if np.any(variation > 0.15):
            continue

        unique_dates = ordered["ds"].drop_duplicates().sort_values().to_list()
        if len(unique_dates) < 2:
            continue

        gaps = np.diff([d.toordinal() for d in unique_dates])
        if len(gaps) == 0:
            continue
        avg_gap = float(np.mean(gaps))

        frequency = ""
        day_of_month = None
        day_of_week = None
        if 25 <= avg_gap <= 35:
            frequency = "monthly"
            day_values = [d.day for d in unique_dates]
            day_of_month = int(round(float(np.median(day_values))))
        elif 6 <= avg_gap <= 8:
            frequency = "weekly"
            day_values = [d.weekday() for d in unique_dates]
            day_of_week = int(round(float(np.median(day_values))))
        else:
            continue

        signed_amount = _safe_float(np.mean(amounts), 0.0)
        if signed_amount == 0.0:
            continue

        recurring_patterns.append(
            {
                "description_key": description_key,
                "description": str(ordered["description"].iloc[-1]),
                "category": str(ordered["category"].iloc[-1]),
                "frequency": frequency,
                "amount": round(signed_amount, 2),
                "day_of_month": day_of_month,
                "day_of_week": day_of_week,
                "type": "income" if signed_amount > 0 else "expense",
            }
        )

    return recurring_patterns


def _recurring_flow_for_date(date: pd.Timestamp, recurring_patterns: List[Dict]) -> float:
    """Compute deterministic recurring flow expected on a specific future date."""
    total = 0.0
    year = int(date.year)
    month = int(date.month)
    month_last_day = calendar.monthrange(year, month)[1]

    for pattern in recurring_patterns:
        amount = _safe_float(pattern.get("amount"), 0.0)
        frequency = str(pattern.get("frequency") or "")

        if frequency == "weekly":
            if int(date.weekday()) == int(pattern.get("day_of_week", -1)):
                total += amount
        elif frequency == "monthly":
            day = int(pattern.get("day_of_month") or 1)
            scheduled_day = min(max(day, 1), month_last_day)
            if int(date.day) == scheduled_day:
                total += amount

    return float(total)


def _build_discretionary_fallback(
    discretionary_daily: pd.DataFrame,
    days: int,
) -> pd.DataFrame:
    """Heuristic fallback for discretionary daily flow forecasts."""
    safe = discretionary_daily.copy()
    if safe.empty:
        safe = pd.DataFrame({"ds": [pd.Timestamp(datetime.utcnow().date())], "amount": [0.0]})

    safe["amount"] = pd.to_numeric(safe["amount"], errors="coerce").fillna(0.0)
    safe["ds"] = pd.to_datetime(safe["ds"], errors="coerce")
    safe = safe.dropna(subset=["ds"]).sort_values("ds")
    if safe.empty:
        safe = pd.DataFrame({"ds": [pd.Timestamp(datetime.utcnow().date())], "amount": [0.0]})

    weekday_means = (
        safe.assign(weekday=safe["ds"].dt.weekday)
        .groupby("weekday")["amount"]
        .mean()
        .to_dict()
    )
    recent_volatility = _safe_float(safe["amount"].tail(30).std(ddof=0), 0.0)
    trend = _safe_float(safe["amount"].tail(14).mean(), 0.0)
    band = max(20.0, recent_volatility * 1.5)

    rows: List[Dict] = []
    start_date = pd.Timestamp(safe["ds"].iloc[-1])
    for offset in range(1, days + 1):
        current_date = start_date + timedelta(days=offset)
        expected_flow = (_safe_float(weekday_means.get(current_date.weekday()), 0.0) * 0.65) + (trend * 0.35)
        rows.append(
            {
                "ds": current_date,
                "yhat": expected_flow,
                "yhat_lower": expected_flow - band,
                "yhat_upper": expected_flow + band,
            }
        )

    return pd.DataFrame(rows)


def _predict_discretionary_flow(
    discretionary_daily: pd.DataFrame,
    days: int,
) -> Tuple[pd.DataFrame, bool]:
    """Predict discretionary daily net cashflow using Prophet, with fallback."""
    if Prophet is None or len(discretionary_daily) < 2:
        return _build_discretionary_fallback(discretionary_daily, days), True

    history = discretionary_daily.rename(columns={"amount": "y"})[["ds", "y"]].copy()
    history["y"] = pd.to_numeric(history["y"], errors="coerce")
    history = history.dropna(subset=["y"])
    if len(history) < 2:
        return _build_discretionary_fallback(discretionary_daily, days), True

    model = Prophet(
        interval_width=0.8,
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
    )
    model.add_seasonality(name="monthly", period=30.5, fourier_order=5)

    try:
        model.fit(history[["ds", "y"]])
        future = model.make_future_dataframe(periods=days, freq="D")
        prediction = model.predict(future).tail(days)
    except Exception:
        logger.exception("Prophet fit/predict failed, falling back to heuristic flow model")
        return _build_discretionary_fallback(discretionary_daily, days), True

    return prediction[["ds", "yhat", "yhat_lower", "yhat_upper"]].reset_index(drop=True), False


def _compose_balance_forecast_rows(
    predicted_flow: pd.DataFrame,
    recurring_patterns: List[Dict],
    starting_balance: float,
) -> List[Dict]:
    """Inject recurring deterministic flow and integrate daily flow into balances."""
    frame = predicted_flow.copy()
    frame["ds"] = pd.to_datetime(frame["ds"], errors="coerce")
    frame = frame.dropna(subset=["ds"]).sort_values("ds").reset_index(drop=True)
    if frame.empty:
        return []

    frame["deterministic_flow"] = frame["ds"].map(lambda d: _recurring_flow_for_date(pd.Timestamp(d), recurring_patterns))
    frame["flow_mid"] = frame["yhat"].map(_safe_float) + frame["deterministic_flow"]
    frame["flow_low"] = frame["yhat_lower"].map(_safe_float) + frame["deterministic_flow"]
    frame["flow_high"] = frame["yhat_upper"].map(_safe_float) + frame["deterministic_flow"]

    mid_balances = starting_balance + np.cumsum(frame["flow_mid"].to_numpy())
    low_balances = starting_balance + np.cumsum(frame["flow_low"].to_numpy())
    high_balances = starting_balance + np.cumsum(frame["flow_high"].to_numpy())

    rows: List[Dict] = []
    for idx, row in frame.iterrows():
        predicted_balance = round(_safe_float(mid_balances[idx]), 2)
        lower_bound = round(_safe_float(low_balances[idx]), 2)
        upper_bound = round(_safe_float(high_balances[idx]), 2)
        flow_mid = _safe_float(row["flow_mid"], 0.0)
        rows.append(
            {
                "date": pd.Timestamp(row["ds"]).strftime("%Y-%m-%d"),
                "predicted_balance": predicted_balance,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                # Backward-compatible aliases consumed by current frontend/UI.
                "balance": predicted_balance,
                "low": lower_bound,
                "high": upper_bound,
                "inflows": round(max(flow_mid, 0.0), 2),
                "outflows": round(min(flow_mid, 0.0), 2),
            }
        )

    return rows


def generate_forecast(
    transactions: List[Dict],
    days: int = 42,
    starting_balance: float = 5000.0,
) -> Dict:
    tx_frame = _prepare_transactions_frame(transactions)
    recurring_patterns = _infer_recurring_patterns(tx_frame)
    recurring_keys = {pattern["description_key"] for pattern in recurring_patterns}

    recurring_tx = tx_frame[tx_frame["description_key"].isin(recurring_keys)].copy()
    start_date = tx_frame["ds"].min()
    end_date = tx_frame["ds"].max()
    daily_total = _daily_flow(tx_frame[["ds", "amount"]], start=start_date, end=end_date)
    daily_recurring = _daily_flow(recurring_tx[["ds", "amount"]], start=start_date, end=end_date)

    discretionary_daily = daily_total.copy()
    discretionary_daily["amount"] = daily_total["amount"].to_numpy() - daily_recurring["amount"].to_numpy()

    predicted_discretionary, used_fallback = _predict_discretionary_flow(discretionary_daily, days)
    forecast_rows = _compose_balance_forecast_rows(predicted_discretionary, recurring_patterns, starting_balance)

    if not forecast_rows:
        forecast_rows = _compose_balance_forecast_rows(
            _build_discretionary_fallback(discretionary_daily, days),
            recurring_patterns,
            starting_balance,
        )
        used_fallback = True

    min_point = min(forecast_rows, key=lambda item: item.get("predicted_balance", item.get("balance", 0.0)))
    recent_volatility = _safe_float(discretionary_daily["amount"].tail(30).std(ddof=0), 0.0)
    if len(discretionary_daily) < 2:
        confidence = 15.0
    elif used_fallback:
        confidence = max(20.0, 55.0 - (recent_volatility / 20.0))
    else:
        confidence = 92.0 - (recent_volatility / 25.0)
        if recurring_patterns:
            confidence += min(4.0, len(recurring_patterns) * 0.6)
        confidence = max(45.0, min(95.0, confidence))

    return {
        "forecast_data": forecast_rows,
        "confidence": round(confidence, 0),
        "min_balance": min_point.get("predicted_balance", min_point.get("balance", 0.0)),
        "min_balance_date": min_point["date"],
        "starting_balance": starting_balance,
        "model": "fallback-hybrid" if used_fallback else "prophet-hybrid",
    }


def run_scenario(base_forecast: Dict, scenario_events: List[Dict] | Dict) -> Tuple[Dict, Dict, Dict]:
    """
    Apply structured one-time and recurring events to a base forecast timeline.

    Expected event shape:
    {
      "type": "one_time_spend"|"one_time_income"|"recurring_spend"|"recurring_income",
      "amount": float,
      "date_offset_days": int,
      "description": str
    }
    """

    base_rows = base_forecast.get("forecast_data", [])
    if not base_rows:
        return base_forecast, base_forecast, base_forecast

    normalized_events = _normalize_scenario_events(scenario_events)
    if not normalized_events:
        return base_forecast, base_forecast, base_forecast

    low_rows = _apply_scenario_events(
        base_rows,
        normalized_events,
        expense_multiplier=1.15,
        income_multiplier=0.90,
    )
    likely_rows = _apply_scenario_events(
        base_rows,
        normalized_events,
        expense_multiplier=1.0,
        income_multiplier=1.0,
    )
    high_rows = _apply_scenario_events(
        base_rows,
        normalized_events,
        expense_multiplier=0.90,
        income_multiplier=1.10,
    )

    low = {
        "forecast_data": low_rows,
        "confidence": max(35, base_forecast.get("confidence", 70) - 8),
    }
    likely = {
        "forecast_data": likely_rows,
        "confidence": base_forecast.get("confidence", 70),
    }
    high = {
        "forecast_data": high_rows,
        "confidence": min(99, base_forecast.get("confidence", 70) + 5),
    }

    return low, likely, high


def _normalize_scenario_events(raw_events: List[Dict] | Dict) -> List[Dict]:
    """Normalize scenario payload into strict internal event records."""
    if isinstance(raw_events, dict):
        # Backward compatibility for legacy single-scenario payloads.
        amount = abs(_safe_float(raw_events.get("amount"), 0.0))
        if amount <= 0:
            return []
        scenario_type = str(raw_events.get("type") or "spend").lower()
        mapped_type = "one_time_income" if scenario_type in {"income", "save"} else "one_time_spend"
        return [
            {
                "type": mapped_type,
                "amount": amount,
                "date_offset_days": 0,
                "description": str(raw_events.get("description") or ""),
            }
        ]

    if not isinstance(raw_events, list):
        return []

    allowed = {
        "one_time_spend",
        "one_time_income",
        "recurring_spend",
        "recurring_income",
    }
    normalized: List[Dict] = []
    for event in raw_events:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "").strip().lower()
        if event_type not in allowed:
            continue
        amount = abs(_safe_float(event.get("amount"), 0.0))
        if amount <= 0:
            continue
        try:
            offset = int(event.get("date_offset_days", 0))
        except (TypeError, ValueError):
            offset = 0
        normalized.append(
            {
                "type": event_type,
                "amount": amount,
                "date_offset_days": max(offset, 0),
                "description": str(event.get("description") or ""),
            }
        )
    return normalized


def _apply_scenario_events(
    base_rows: List[Dict],
    events: List[Dict],
    expense_multiplier: float,
    income_multiplier: float,
) -> List[Dict]:
    """Apply event effects day-by-day to generate a new scenario curve."""
    anchor_date = pd.to_datetime(base_rows[0].get("date"), errors="coerce")
    if pd.isna(anchor_date):
        anchor_date = pd.Timestamp(datetime.utcnow().date())
    anchor_date = anchor_date.normalize().date()

    running_adjustment = 0.0
    transformed_rows: List[Dict] = []

    for item in base_rows:
        updated = dict(item)
        current_ts = pd.to_datetime(item.get("date"), errors="coerce")
        if pd.isna(current_ts):
            transformed_rows.append(updated)
            continue
        current_date = current_ts.normalize().date()

        day_adjustment = 0.0
        for event in events:
            start_date = anchor_date + timedelta(days=int(event.get("date_offset_days", 0)))
            if current_date < start_date:
                continue

            event_type = str(event.get("type"))
            amount = _safe_float(event.get("amount"), 0.0)
            if amount <= 0:
                continue

            if event_type in {"one_time_income", "recurring_income"}:
                signed_amount = amount * income_multiplier
            else:
                signed_amount = -amount * expense_multiplier

            if event_type.startswith("one_time"):
                if current_date == start_date:
                    day_adjustment += signed_amount
            else:
                # Monthly recurring impact amortized into daily increments.
                day_adjustment += signed_amount / 30.5

        running_adjustment += day_adjustment

        for key in ("predicted_balance", "balance", "lower_bound", "low", "upper_bound", "high"):
            if key in updated:
                updated[key] = round(_safe_float(updated.get(key), 0.0) + running_adjustment, 2)

        if "inflows" in updated or "outflows" in updated:
            base_flow = _safe_float(updated.get("inflows"), 0.0) + _safe_float(updated.get("outflows"), 0.0)
            scenario_flow = base_flow + day_adjustment
            updated["inflows"] = round(max(scenario_flow, 0.0), 2)
            updated["outflows"] = round(min(scenario_flow, 0.0), 2)

        transformed_rows.append(updated)

    return transformed_rows


def extract_alerts(forecast: Dict) -> List[Dict]:
    alerts: List[Dict] = []
    for item in forecast.get("forecast_data", []):
        balance = _safe_float(item.get("predicted_balance", item.get("balance", 0.0)), 0.0)
        if balance < 0:
            alerts.append(
                {
                    "date": item.get("date"),
                    "severity": "critical",
                    "title": "Overdraft risk",
                    "message": f"Projected balance drops below zero on {item.get('date')}",
                    "action": "Move bill",
                }
            )
        elif balance < 500:
            alerts.append(
                {
                    "date": item.get("date"),
                    "severity": "warning",
                    "title": "Tight cash buffer",
                    "message": f"Projected balance is getting tight on {item.get('date')}",
                    "action": "Postpone expense",
                }
            )

    return alerts[:5]
