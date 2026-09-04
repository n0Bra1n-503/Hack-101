"""API endpoints for disaster risk intelligence and citizen public safety."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.risk import DisasterRisk
from backend.app.services.risk_service import risk_service

router = APIRouter(tags=["risks", "public_safety"])


@router.get("/risks")
def get_all_active_risks(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retrieve all validated disaster risks."""
    return risk_service.get_all_risks(db)


@router.get("/risks/{risk_id}")
def get_risk_detail(risk_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve detailed assessment for a specific disaster risk event."""
    risk = db.query(DisasterRisk).filter(DisasterRisk.risk_id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail={"error": "risk_not_found", "message": f"Risk '{risk_id}' not found"})
    return {
        "id": risk.risk_id,
        "area": risk.area,
        "risk_level": risk.risk_level,
        "event_type": risk.event_type,
        "confidence": risk.confidence,
        "trigger_reading_id": risk.trigger_reading_id,
        "supporting_stations": risk.supporting_stations,
        "message": risk.public_message,
        "safety_guidance": risk.safety_guidance,
        "advisory_status": risk.advisory_status,
        "created_at": risk.created_at.isoformat(),
    }


@router.get("/areas/{area}/risk")
@router.get("/risks/area/{area}")
def get_area_risk(area: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get internal disaster risk assessment for a specific geographic area."""
    return risk_service.get_public_safety_view(area, db)


@router.get("/public/risk/{area}")
def get_public_citizen_risk(area: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Public citizen-safe advisory endpoint.

    Strictly suppresses internal ML scores, sensor IDs, and diagnostic details.
    """
    return risk_service.get_public_safety_view(area, db)
