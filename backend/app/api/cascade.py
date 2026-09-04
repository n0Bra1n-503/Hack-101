"""API endpoints for illustrative cascade pipeline walkthroughs."""

from typing import Any, Dict
from fastapi import APIRouter
from backend.app.services.cascade_service import cascade_service

router = APIRouter(tags=["cascade"])


@router.get("/cascade/{scenario_id}")
def get_cascade_scenario(scenario_id: str) -> Dict[str, Any]:
    """Retrieve end-to-end cascade walkthrough for Scenario A, B, or C."""
    return cascade_service.get_scenario(scenario_id)
