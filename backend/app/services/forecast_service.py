"""Forecasting service used by the demo backend."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - fallback when Prophet cannot load
    Prophet = None


class ForecastService:
    """Service for financial forecasting."""

    def __init__(self, starting_balance: float = 5000.0) -> None:
        self.starting_balance = starting_balance

    def _prepare_series(self, transactions: List[Dict]) -> pd.DataFrame:
        if not transactions:
            today = pd.Timestamp(datetime.utcnow().date())
            return pd.DataFrame({"ds": [today], "amount": [0.0]})

        frame = pd.DataFrame(transactions).copy()
        frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
        daily = frame.groupby("date", as_index=False)["amount"].sum().sort_values("date")
        full_range = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
        daily = daily.set_index("date").reindex(full_range, fill_value=0.0)
        daily.index.name = "ds"
        return daily.reset_index()

    def _historical_balance_series(self, daily: pd.DataFrame) -> pd.DataFrame:
        frame = daily.copy()
        frame["y"] = self.starting_balance + frame["amount"].cumsum()
        return frame[["ds", "y", "amount"]]

    def _build_fallback_rows(self, daily: pd.DataFrame, days: int) -> List[Dict]:
        running_balance = float(self.starting_balance + daily["amount"].sum())
        weekday_means = daily.assign(weekday=daily["ds"].dt.weekday).groupby("weekday")["amount"].mean().to_dict()
        recent_volatility = float(daily["amount"].tail(30).std(ddof=0) or 100.0)
        trend = float(daily["amount"].tail(14).mean() or 0.0)

        forecast_rows: List[Dict] = []
        start_date = daily["ds"].iloc[-1]

        for offset in range(1, days + 1):
            date = start_date + timedelta(days=offset)
            expected_flow = (weekday_means.get(date.weekday(), 0.0) * 0.65) + (trend * 0.35)
            running_balance += expected_flow

            confidence_band = max(120.0, recent_volatility * 1.5)
            forecast_rows.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "balance": round(running_balance, 2),
                    "low": round(running_balance - confidence_band, 2),
                    "high": round(running_balance + confidence_band, 2),
                    "inflows": round(max(expected_flow, 0.0), 2),
                    "outflows": round(min(expected_flow, 0.0), 2),
                }
            )

        return forecast_rows

    def _prophet_rows(self, daily: pd.DataFrame, days: int) -> List[Dict]:
        if Prophet is None:
            return self._build_fallback_rows(daily, days)

        history = self._historical_balance_series(daily)
        model = Prophet(interval_width=0.8, daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        model.fit(history[["ds", "y"]])

        future = model.make_future_dataframe(periods=days, freq="D")
        prediction = model.predict(future).tail(days)

        forecast_rows: List[Dict] = []
        for row in prediction.itertuples(index=False):
            forecast_rows.append(
                {
                    "date": row.ds.strftime("%Y-%m-%d"),
                    "balance": round(float(row.yhat), 2),
                    "low": round(float(row.yhat_lower), 2),
                    "high": round(float(row.yhat_upper), 2),
                    "inflows": round(max(float(row.yhat) - float(row.yhat_lower), 0.0), 2),
                    "outflows": round(min(float(row.yhat) - float(row.yhat_upper), 0.0), 2),
                }
            )

        return forecast_rows

    def generate_forecast(self, transactions: List[Dict], days: int = 42) -> Dict:
        """Generate a balance forecast from transaction history."""

        daily = self._prepare_series(transactions)
        forecast_rows = self._prophet_rows(daily, days)

        min_point = min(forecast_rows, key=lambda item: item["balance"])
        recent_volatility = float(daily["amount"].tail(30).std(ddof=0) or 0.0)
        confidence = max(45.0, min(95.0, 95.0 - (recent_volatility / 25.0)))

        return {
            "forecast_data": forecast_rows,
            "confidence": round(confidence, 0),
            "min_balance": min_point["balance"],
            "min_balance_date": min_point["date"],
            "starting_balance": self.starting_balance,
            "model": "prophet" if Prophet is not None else "fallback",
        }

    def run_scenario(self, forecast: Dict, scenario: Dict) -> Tuple[Dict, Dict, Dict]:
        """Run scenario analysis on a forecast."""

        base_rows = forecast.get("forecast_data", [])
        if not base_rows:
            return forecast, forecast, forecast

        scenario_date = scenario.get("date") or base_rows[0]["date"]
        scenario_amount = float(scenario.get("amount", 0.0))
        scenario_type = scenario.get("type", "spend")

        if scenario_type in {"save", "income"}:
            impact = scenario_amount
        elif scenario_type == "delay":
            impact = 0.0
        else:
            impact = -scenario_amount

        def shifted_rows(multiplier: float) -> List[Dict]:
            rows: List[Dict] = []
            applied = False
            for item in base_rows:
                updated = dict(item)
                if item["date"] >= scenario_date:
                    applied = True
                if applied:
                    updated["balance"] = round(updated["balance"] + (impact * multiplier), 2)
                    updated["low"] = round(updated["low"] + (impact * multiplier), 2)
                    updated["high"] = round(updated["high"] + (impact * multiplier), 2)
                rows.append(updated)
            return rows

        low = {"forecast_data": shifted_rows(-0.15), "confidence": max(35, forecast.get("confidence", 70) - 8)}
        likely = {"forecast_data": shifted_rows(1.0), "confidence": forecast.get("confidence", 70)}
        high = {"forecast_data": shifted_rows(0.15), "confidence": min(99, forecast.get("confidence", 70) + 5)}

        return low, likely, high

    def extract_alerts(self, forecast: Dict) -> List[Dict]:
        """Extract early warnings from a forecast."""

        alerts: List[Dict] = []
        for item in forecast.get("forecast_data", []):
            balance = float(item.get("balance", 0.0))
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
