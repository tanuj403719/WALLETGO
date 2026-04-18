"""
Scenario persistence endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from schemas.requests import CompareScenariosRequest, SaveScenarioRequest
from services.scenario_service import compare_scenarios, get_scenario_run, list_scenario_runs, save_scenario_run

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.post("/save")
async def save_scenario(request: SaveScenarioRequest):
    return save_scenario_run(
        user_id=request.user_id,
        title=request.title,
        description=request.description,
        language=request.language,
        low_result=request.low_result,
        likely_result=request.likely_result,
        high_result=request.high_result,
        explanation=request.explanation,
        intent=request.intent,
    )


@router.get("/saved")
async def saved_scenarios(
    user_id: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
):
    return list_scenario_runs(user_id=user_id, limit=limit)


@router.get("/saved/{scenario_id}")
async def saved_scenario_detail(scenario_id: str, user_id: str = Query(..., min_length=1)):
    return get_scenario_run(user_id=user_id, scenario_id=scenario_id)


@router.get("/compare")
async def compare_saved_scenarios(
    user_id: str = Query(..., min_length=1),
    left_id: str = Query(..., min_length=1),
    right_id: str = Query(..., min_length=1),
):
    request = CompareScenariosRequest(user_id=user_id, left_id=left_id, right_id=right_id)
    return compare_scenarios(user_id=request.user_id, left_id=request.left_id, right_id=request.right_id)
