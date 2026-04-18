"""
Scenario persistence and comparison logic backed by Supabase.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from services.supabase_service import get_supabase_client

SCENARIO_RUNS_TABLE = "scenario_runs"
_SCENARIO_FALLBACK_STORE: Dict[str, List[Dict[str, Any]]] = {}


def _extract_title(description: str, likely_result: Dict[str, Any]) -> str:
    meta = likely_result.get("_saved_scenario") if isinstance(likely_result, dict) else None
    if isinstance(meta, dict):
        value = str(meta.get("title") or "").strip()
        if value:
            return value

    cleaned = " ".join(str(description or "").strip().split())
    return cleaned[:60] if cleaned else "Saved Scenario"


def _row_to_summary(row: Dict[str, Any]) -> Dict[str, Any]:
    description = str(row.get("description") or "")
    likely_result = row.get("likely_result") or {}
    return {
        "id": row.get("id"),
        "title": _extract_title(description, likely_result),
        "description": description,
        "language": row.get("language") or "en",
        "created_at": row.get("created_at"),
        "line_color": likely_result.get("line_color", "white"),
        "net_difference": likely_result.get("net_difference", 0.0),
    }


def _serialize_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a record to the same shape returned by Supabase rows."""
    return {
        "id": row.get("id") or str(uuid4()),
        "user_id": row.get("user_id"),
        "description": str(row.get("description") or ""),
        "language": row.get("language") or "en",
        "low_result": row.get("low_result") or {},
        "likely_result": row.get("likely_result") or {},
        "high_result": row.get("high_result") or {},
        "explanation": row.get("explanation") or "",
        "created_at": row.get("created_at") or datetime.now(timezone.utc).isoformat(),
    }


def _fallback_insert(payload: Dict[str, Any]) -> Dict[str, Any]:
    record = _serialize_record(payload)
    user_id = str(record.get("user_id") or "")
    _SCENARIO_FALLBACK_STORE.setdefault(user_id, []).append(record)
    _SCENARIO_FALLBACK_STORE[user_id].sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return record


def _fallback_list(user_id: str, limit: int) -> List[Dict[str, Any]]:
    records = _SCENARIO_FALLBACK_STORE.get(user_id, [])
    return records[:limit]


def _fallback_get(user_id: str, scenario_id: str) -> Optional[Dict[str, Any]]:
    records = _SCENARIO_FALLBACK_STORE.get(user_id, [])
    for row in records:
        if str(row.get("id")) == str(scenario_id):
            return row
    return None


def _final_balance(scenario_payload: Dict[str, Any]) -> float:
    rows = scenario_payload.get("forecast_data", []) if isinstance(scenario_payload, dict) else []
    if not rows:
        return 0.0
    last = rows[-1]
    try:
        return float(last.get("predicted_balance", last.get("balance", 0.0)) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _balance_series(scenario_payload: Dict[str, Any]) -> List[float]:
    rows = scenario_payload.get("forecast_data", []) if isinstance(scenario_payload, dict) else []
    values: List[float] = []
    for row in rows:
        try:
            values.append(float(row.get("predicted_balance", row.get("balance", 0.0)) or 0.0))
        except (TypeError, ValueError):
            continue
    return values


def _min_balance(scenario_payload: Dict[str, Any]) -> float:
    values = _balance_series(scenario_payload)
    if not values:
        return 0.0
    return min(values)


def _avg_balance(scenario_payload: Dict[str, Any]) -> float:
    values = _balance_series(scenario_payload)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _negative_days(scenario_payload: Dict[str, Any]) -> int:
    values = _balance_series(scenario_payload)
    return len([v for v in values if v < 0])


def _low_buffer_days(scenario_payload: Dict[str, Any], buffer_threshold: float = 500.0) -> int:
    values = _balance_series(scenario_payload)
    return len([v for v in values if v < buffer_threshold])


def _daily_variability(scenario_payload: Dict[str, Any]) -> float:
    values = _balance_series(scenario_payload)
    if len(values) < 2:
        return 0.0
    deltas = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    if not deltas:
        return 0.0
    return sum(deltas) / len(deltas)


def _realism_score(scenario_payload: Dict[str, Any]) -> Dict[str, float]:
    """
    Risk-adjusted score to avoid naive 'highest final balance always wins'.

    We reward healthy end/average balances and penalize:
    - overdraft days heavily
    - low-buffer days moderately
    - high day-to-day volatility lightly
    """
    final_balance = _final_balance(scenario_payload)
    avg_balance = _avg_balance(scenario_payload)
    min_balance = _min_balance(scenario_payload)
    negative_days = _negative_days(scenario_payload)
    low_buffer_days = _low_buffer_days(scenario_payload)
    variability = _daily_variability(scenario_payload)

    score = (
        (final_balance * 0.30)
        + (avg_balance * 0.40)
        + (min_balance * 0.30)
        - (negative_days * 600.0)
        - (low_buffer_days * 60.0)
        - (variability * 0.20)
    )

    return {
        "score": round(score, 2),
        "final_balance": round(final_balance, 2),
        "average_balance": round(avg_balance, 2),
        "min_balance": round(min_balance, 2),
        "negative_days": int(negative_days),
        "low_buffer_days": int(low_buffer_days),
        "daily_variability": round(variability, 2),
    }


def _net_difference(scenario_payload: Dict[str, Any]) -> float:
    """Return scenario-vs-base net difference when available, else infer from series."""
    if isinstance(scenario_payload, dict):
        try:
            explicit = float(scenario_payload.get("net_difference", 0.0) or 0.0)
            if explicit != 0.0:
                return explicit
        except (TypeError, ValueError):
            pass

    values = _balance_series(scenario_payload)
    if len(values) >= 2:
        return values[-1] - values[0]
    return 0.0


def _line_color_rank(scenario_payload: Dict[str, Any]) -> int:
    color = str((scenario_payload or {}).get("line_color", "white")).strip().lower()
    if color == "green":
        return 1
    if color == "red":
        return -1
    return 0


def save_scenario_run(
    user_id: str,
    title: Optional[str],
    description: str,
    language: str,
    low_result: Dict[str, Any],
    likely_result: Dict[str, Any],
    high_result: Dict[str, Any],
    explanation: str = "",
    intent: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    likely_payload = dict(likely_result or {})
    likely_payload["_saved_scenario"] = {
        "title": (title or "").strip() or " ".join(description.strip().split())[:60] or "Saved Scenario",
        "intent": intent or {},
    }

    payload = {
        "user_id": user_id,
        "description": description,
        "language": language or "en",
        "low_result": low_result or {},
        "likely_result": likely_payload,
        "high_result": high_result or {},
        "explanation": explanation or "",
    }

    row = None
    try:
        client = get_supabase_client()
        response = client.table(SCENARIO_RUNS_TABLE).insert(payload).execute()
        row = (response.data or [None])[0]
    except Exception:
        row = _fallback_insert(payload)

    if not row:
        row = _fallback_insert(payload)

    return {
        "saved": True,
        "scenario": _row_to_summary(row),
    }


def list_scenario_runs(user_id: str, limit: int = 10) -> Dict[str, Any]:
    safe_limit = max(1, min(limit, 50))

    rows: List[Dict[str, Any]] = []
    try:
        client = get_supabase_client()
        response = (
            client.table(SCENARIO_RUNS_TABLE)
            .select("id,description,language,likely_result,created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(safe_limit)
            .execute()
        )
        rows = response.data or []
    except Exception:
        rows = _fallback_list(user_id, safe_limit)

    if not rows:
        rows = _fallback_list(user_id, safe_limit)

    return {"items": [_row_to_summary(row) for row in rows]}


def get_scenario_run(user_id: str, scenario_id: str) -> Dict[str, Any]:
    row = None
    try:
        client = get_supabase_client()
        response = (
            client.table(SCENARIO_RUNS_TABLE)
            .select("id,description,language,low_result,likely_result,high_result,explanation,created_at")
            .eq("user_id", user_id)
            .eq("id", scenario_id)
            .limit(1)
            .execute()
        )
        row = (response.data or [None])[0]
    except Exception:
        row = _fallback_get(user_id, scenario_id)

    if not row:
        row = _fallback_get(user_id, scenario_id)

    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return {
        "scenario": {
            "id": row.get("id"),
            "title": _extract_title(str(row.get("description") or ""), row.get("likely_result") or {}),
            "description": row.get("description") or "",
            "language": row.get("language") or "en",
            "created_at": row.get("created_at"),
            "low": row.get("low_result") or {},
            "likely": row.get("likely_result") or {},
            "high": row.get("high_result") or {},
            "explanation": row.get("explanation") or "",
        }
    }


def compare_scenarios(user_id: str, left_id: str, right_id: str) -> Dict[str, Any]:
    left = get_scenario_run(user_id, left_id).get("scenario", {})
    right = get_scenario_run(user_id, right_id).get("scenario", {})

    left_likely = left.get("likely") or {}
    right_likely = right.get("likely") or {}

    left_metrics = _realism_score(left_likely)
    right_metrics = _realism_score(right_likely)
    left_final = left_metrics["final_balance"]
    right_final = right_metrics["final_balance"]

    score_delta = left_metrics["score"] - right_metrics["score"]
    left_net_diff = _net_difference(left_likely)
    right_net_diff = _net_difference(right_likely)

    # Primary winner selection by risk-adjusted score.
    if score_delta > 0.5:
        winner = "left"
    elif score_delta < -0.5:
        winner = "right"
    else:
        # Tie-break chain for near-equal scores:
        # 1) fewer overdraft days
        # 2) higher minimum balance
        # 3) higher final balance
        # 4) higher net difference vs base
        # 5) line color rank (green > white > red)
        if left_metrics["negative_days"] < right_metrics["negative_days"]:
            winner = "left"
        elif right_metrics["negative_days"] < left_metrics["negative_days"]:
            winner = "right"
        elif left_metrics["min_balance"] > right_metrics["min_balance"] + 5:
            winner = "left"
        elif right_metrics["min_balance"] > left_metrics["min_balance"] + 5:
            winner = "right"
        elif left_metrics["final_balance"] > right_metrics["final_balance"] + 5:
            winner = "left"
        elif right_metrics["final_balance"] > left_metrics["final_balance"] + 5:
            winner = "right"
        elif left_net_diff > right_net_diff + 1:
            winner = "left"
        elif right_net_diff > left_net_diff + 1:
            winner = "right"
        else:
            left_color_rank = _line_color_rank(left_likely)
            right_color_rank = _line_color_rank(right_likely)
            if left_color_rank > right_color_rank:
                winner = "left"
            elif right_color_rank > left_color_rank:
                winner = "right"
            else:
                winner = "tie"

    comparison = {
        "left_final_balance": round(left_final, 2),
        "right_final_balance": round(right_final, 2),
        "difference": round(left_final - right_final, 2),
        "winner": winner,
        "left_min_balance": left_metrics["min_balance"],
        "right_min_balance": right_metrics["min_balance"],
        "left_negative_days": left_metrics["negative_days"],
        "right_negative_days": right_metrics["negative_days"],
        "left_low_buffer_days": left_metrics["low_buffer_days"],
        "right_low_buffer_days": right_metrics["low_buffer_days"],
        "left_average_balance": left_metrics["average_balance"],
        "right_average_balance": right_metrics["average_balance"],
        "left_risk_adjusted_score": left_metrics["score"],
        "right_risk_adjusted_score": right_metrics["score"],
        "left_net_difference": round(left_net_diff, 2),
        "right_net_difference": round(right_net_diff, 2),
    }

    left_series = _balance_series(left_likely)
    right_series = _balance_series(right_likely)
    is_identical_projection = bool(left_series) and (left_series == right_series)
    comparison["is_identical_projection"] = is_identical_projection

    if comparison["winner"] == "left":
        reason = []
        if left_metrics["negative_days"] < right_metrics["negative_days"]:
            reason.append("fewer overdraft days")
        if left_metrics["min_balance"] > right_metrics["min_balance"]:
            reason.append("higher safety floor")
        if left_metrics["average_balance"] > right_metrics["average_balance"]:
            reason.append("better average balance")
        why = ", ".join(reason) if reason else "better overall risk-adjusted profile"
        summary_text = (
            f"{left.get('title', 'Left scenario')} performs better by ${abs(comparison['difference']):.2f} "
            f"at forecast end, with final balance ${comparison['left_final_balance']:.2f} vs ${comparison['right_final_balance']:.2f}. "
            f"It wins mainly due to {why}."
        )
    elif comparison["winner"] == "right":
        reason = []
        if right_metrics["negative_days"] < left_metrics["negative_days"]:
            reason.append("fewer overdraft days")
        if right_metrics["min_balance"] > left_metrics["min_balance"]:
            reason.append("higher safety floor")
        if right_metrics["average_balance"] > left_metrics["average_balance"]:
            reason.append("better average balance")
        why = ", ".join(reason) if reason else "better overall risk-adjusted profile"
        summary_text = (
            f"{right.get('title', 'Right scenario')} performs better by ${abs(comparison['difference']):.2f} "
            f"at forecast end, with final balance ${comparison['right_final_balance']:.2f} vs ${comparison['left_final_balance']:.2f}. "
            f"It wins mainly due to {why}."
        )
    else:
        summary_text = (
            f"Both scenarios are very close on risk-adjusted score (left {left_metrics['score']:.2f}, right {right_metrics['score']:.2f}). "
            "Choose based on preference and non-financial priorities."
        )

    if is_identical_projection:
        summary_text += " The saved projections are numerically identical; re-run each scenario and save immediately after running it."

    return {
        "left": left,
        "right": right,
        "comparison": comparison,
        "summary_text": summary_text,
    }
