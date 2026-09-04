"""API endpoints for illustrative cascade pipeline walkthroughs."""

from typing import Any, Dict
from fastapi import APIRouter
from backend.app.services.cascade_service import cascade_service

from pydantic import BaseModel

router = APIRouter(tags=["cascade"])


class ScenarioInjectRequest(BaseModel):
    scenario: str


@router.get("/cascade/{scenario_id}")
def get_cascade_scenario(scenario_id: str) -> Dict[str, Any]:
    """Retrieve end-to-end cascade walkthrough for Scenario A, B, or C."""
    return cascade_service.get_scenario(scenario_id)


@router.post("/scenarios/inject")
def inject_scenario(req: ScenarioInjectRequest) -> Dict[str, Any]:
    """Trigger or retrieve an illustrative pipeline scenario for the UI."""
    scenario_map = {
        "spike_55c": "A",
        "genuine_heat_event": "B",
        "degradation": "C",
    }
    scen_id = scenario_map.get(req.scenario, req.scenario)
    return cascade_service.get_scenario(scen_id)
