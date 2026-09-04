"""Disaster Risk Assessment and Public Citizen Safety Service.

Implements strict validation gating:
Only validated genuine_weather events may trigger disaster risk assessments.
Sensor faults and uncertain anomalies strictly block automatic risk and public alerts.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.risk import DisasterRisk

logger = logging.getLogger("skyguard.risk_service")


class DisasterRiskService:
    """Evaluates disaster risk strictly from validated genuine weather phenomena."""

    def evaluate_weather_risk(
        self,
        reading: Dict[str, Any],
        decision_result: Dict[str, Any],
        db: Session,
    ) -> Optional[DisasterRisk]:
        """Assess disaster risk for a weather reading.
        
        Strict architectural rule:
        If decision is 'sensor_fault' or 'uncertain', automatic disaster risk is BLOCKED.
        """
        decision = decision_result.get("decision")
        if decision != "genuine_weather":
            logger.info(
                f"Disaster risk assessment BLOCKED for reading {reading.get('reading_id')}: "
                f"Decision is '{decision}' (requires 'genuine_weather')."
            )
            return None

        temp = reading.get("temperature")
        rainfall = reading.get("rainfall")
        wind = reading.get("wind_speed")
        area = reading.get("area") or "Regional Zone"
        station_id = reading.get("station_id")

        event_type = None
        risk_level = "LOW"
        public_msg = ""
        safety_guide = ""

        # Meteorological Risk Assessment Matrix
        if temp is not None and temp >= 44.0:
            event_type = "extreme_heatwave"
            risk_level = "HIGH"
            public_msg = f"Severe Heatwave Alert for {area}: Ambient temperature has reached {temp:.1f}°C."
            safety_guide = "Avoid direct sun exposure between 11:00 AM and 4:00 PM. Drink plenty of water and seek shaded or air-conditioned environments."
        elif temp is not None and temp >= 40.0:
            event_type = "heat_advisory"
            risk_level = "MEDIUM"
            public_msg = f"Elevated Heat Advisory for {area}: Regional temperatures recorded at {temp:.1f}°C."
            safety_guide = "Stay hydrated and minimize prolonged outdoor physical exertion."

        elif rainfall is not None and rainfall >= 100.0:
            event_type = "flash_flood_risk"
            risk_level = "HIGH"
            public_msg = f"Flash Flood Warning for {area}: Intense cumulative precipitation of {rainfall:.1f} mm detected."
            safety_guide = "Stay away from low-lying areas, river banks, and storm drains. Do not attempt to drive through flooded roads."
        elif rainfall is not None and rainfall >= 50.0:
            event_type = "heavy_rainfall"
            risk_level = "MEDIUM"
            public_msg = f"Heavy Rainfall Advisory for {area}: {rainfall:.1f} mm precipitation recorded."
            safety_guide = "Exercise caution while commuting and watch for localized waterlogging."

        elif wind is not None and wind >= 25.0:
            event_type = "gale_storm"
            risk_level = "HIGH"
            public_msg = f"High Wind Warning for {area}: Sustained wind gusts of {wind:.1f} m/s."
            safety_guide = "Secure loose outdoor objects and remain indoors away from windows."

        if not event_type:
            return None

        # Create persistent risk record
        now = datetime.utcnow()
        risk_record = DisasterRisk(
            risk_id=f"RISK-{area.replace(' ', '_')}-{int(now.timestamp())}",
            area=area,
            risk_level=risk_level,
            event_type=event_type,
            confidence=decision_result.get("confidence", 0.9),
            trigger_reading_id=reading.get("reading_id"),
            supporting_stations=json.dumps([station_id]),
            public_message=public_msg,
            safety_guidance=safety_guide,
            advisory_status="advisory_active" if risk_level == "HIGH" else "monitoring",
            created_at=now,
        )

        db.add(risk_record)
        db.commit()
        db.refresh(risk_record)
        logger.warning(f"VALIDATED DISASTER RISK GENERATED: {risk_record.risk_id} [{risk_level}] - {event_type} in {area}")
        return risk_record

    def get_public_safety_view(self, area: str, db: Session) -> Dict[str, Any]:
        """Return citizen-safe public summary without internal diagnostic telemetry."""
        risk = (
            db.query(DisasterRisk)
            .filter(DisasterRisk.area == area)
            .order_by(DisasterRisk.created_at.desc())
            .first()
        )
        if not risk:
            return {
                "area": area,
                "risk_level": "LOW",
                "event_type": "nominal_weather",
                "confidence": 0.95,
                "message": f"Normal weather conditions reported across {area}.",
                "safety_guidance": "No active meteorological advisories. Standard seasonal safety precautions apply.",
                "advisory_status": "none",
            }

        # Strictly sanitize internal fields
        return {
            "area": risk.area,
            "risk_level": risk.risk_level,
            "event_type": risk.event_type,
            "confidence": risk.confidence,
            "message": risk.public_message,
            "safety_guidance": risk.safety_guidance,
            "advisory_status": risk.advisory_status,
            "issued_at": risk.created_at.isoformat(),
        }

    def get_all_risks(self, db: Session) -> List[Dict[str, Any]]:
        """Return all active risk events for operator dashboard."""
        risks = db.query(DisasterRisk).order_by(DisasterRisk.created_at.desc()).limit(20).all()
        return [
            {
                "id": r.risk_id,
                "area": r.area,
                "risk_level": r.risk_level,
                "event_type": r.event_type,
                "confidence": r.confidence,
                "trigger_reading_id": r.trigger_reading_id,
                "message": r.public_message,
                "safety_guidance": r.safety_guidance,
                "advisory_status": r.advisory_status,
                "created_at": r.created_at.isoformat(),
            }
            for r in risks
        ]


risk_service = DisasterRiskService()
