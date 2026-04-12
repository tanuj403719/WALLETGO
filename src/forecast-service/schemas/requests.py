"""
Pydantic request schemas for the forecast-service.
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class ForecastGenerateRequest(BaseModel):
    transactions: List[Dict]
    days: int = 42
    starting_balance: float = 5000.0


class ForecastHistoryRequest(BaseModel):
    transactions: List[Dict]
    limit: int = 10


class ScenarioRunRequest(BaseModel):
    base_forecast: Dict
    scenario_events: List[Dict]

    @property
    def scenario(self) -> List[Dict]:
        """Backward-compatible alias used by existing route code."""
        return self.scenario_events
