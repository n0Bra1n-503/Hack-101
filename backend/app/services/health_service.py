"""Digital Twin and Predictive Maintenance Service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.maintenance import MaintenanceTask
from backend.app.models.sensor_health import SensorHealth

logger = logging.getLogger("skyguard.health_service")


class SensorHealthService:
    """Tracks station digital twin health and predictive maintenance queues."""

    def record_observation_health(
        self,
        station_id: str,
        decision_result: Dict[str, Any],
        db: Session,
    ) -> SensorHealth:
        """Update digital twin metrics based on newest decision intelligence result."""
        health = db.query(SensorHealth).filter(SensorHealth.station_id == station_id).first()
        now = datetime.utcnow()

        if not health:
            health = SensorHealth(
                health_id=f"SH-{station_id}",
                station_id=station_id,
                recent_health_score=100.0,
                historical_health_score=100.0,
                total_readings=0,
                anomaly_count=0,
                fault_count=0,
                maintenance_priority="LOW",
                updated_at=now,
            )
            db.add(health)

        health.total_readings += 1

        is_fault = decision_result.get("decision") == "sensor_fault"
        fault_type = decision_result.get("fault_type")
        trust_score = decision_result.get("trust_score", 100.0)

        if is_fault:
            health.fault_count += 1
            health.anomaly_count += 1
            health.last_fault_type = fault_type
            health.last_fault_timestamp = now
            # Exponential decay on health
            health.recent_health_score = max(0.0, health.recent_health_score - 15.0)
        elif decision_result.get("decision") == "uncertain":
            health.anomaly_count += 1
            health.recent_health_score = max(0.0, health.recent_health_score - 5.0)
        else:
            # Gradual health recovery
            health.recent_health_score = min(100.0, health.recent_health_score + 1.0)

        # Historical health rolling average
        health.historical_health_score = round(
            (health.historical_health_score * 0.95) + (health.recent_health_score * 0.05), 1
        )
        health.recent_health_score = round(health.recent_health_score, 1)

        # Priority calculation
        if health.recent_health_score < 30.0 or health.fault_count >= 5:
            health.maintenance_priority = "CRITICAL"
        elif health.recent_health_score < 60.0 or health.fault_count >= 2:
            health.maintenance_priority = "HIGH"
        elif health.recent_health_score < 80.0:
            health.maintenance_priority = "MEDIUM"
        else:
            health.maintenance_priority = "LOW"

        health.updated_at = now

        # Add to maintenance queue if high/critical priority and not already pending
        if health.maintenance_priority in ("HIGH", "CRITICAL"):
            existing_task = (
                db.query(MaintenanceTask)
                .filter(MaintenanceTask.station_id == station_id, MaintenanceTask.status == "pending")
                .first()
            )
            if not existing_task:
                task = MaintenanceTask(
                    maintenance_id=f"MNT-{station_id}-{int(now.timestamp())}",
                    station_id=station_id,
                    priority=health.maintenance_priority,
                    status="pending",
                    issue_description=f"Degraded telemetry: health score {health.recent_health_score}% due to {fault_type or 'persistent anomalies'}.",
                    fault_type=fault_type or "sensor_degradation",
                    recommended_action="Dispatch field technician for sensor calibration and connection diagnosis.",
                    created_at=now,
                )
                db.add(task)

        db.commit()
        db.refresh(health)
        return health

    def get_station_health(self, station_id: str, db: Session) -> Dict[str, Any]:
        """Return Digital Twin status for station."""
        health = db.query(SensorHealth).filter(SensorHealth.station_id == station_id).first()
        if not health:
            return {
                "station_id": station_id,
                "health_score": 98.5,
                "status": "HEALTHY",
                "total_readings": 0,
                "anomaly_count": 0,
                "fault_count": 0,
                "maintenance_priority": "LOW",
                "sensors": [
                    {"name": "Temperature", "status": "nominal", "drift": 0.02},
                    {"name": "Pressure", "status": "nominal", "drift": 0.01},
                    {"name": "Humidity", "status": "nominal", "drift": 0.03},
                ],
            }

        status = "HEALTHY" if health.recent_health_score > 75 else ("WARNING" if health.recent_health_score > 40 else "CRITICAL")
        return {
            "station_id": station_id,
            "health_score": health.recent_health_score,
            "historical_score": health.historical_health_score,
            "status": status,
            "total_readings": health.total_readings,
            "anomaly_count": health.anomaly_count,
            "fault_count": health.fault_count,
            "last_fault": health.last_fault_type,
            "maintenance_priority": health.maintenance_priority,
            "sensors": [
                {"name": "Temperature", "status": "degraded" if health.last_fault_type and "temp" in health.last_fault_type else "nominal", "drift": 0.04},
                {"name": "Pressure", "status": "nominal", "drift": 0.01},
                {"name": "Humidity", "status": "nominal", "drift": 0.02},
            ],
        }

    def get_maintenance_queue(self, db: Session) -> List[Dict[str, Any]]:
        """Return active maintenance tasks."""
        tasks = db.query(MaintenanceTask).order_by(MaintenanceTask.created_at.desc()).all()
        return [
            {
                "id": t.maintenance_id,
                "station_id": t.station_id,
                "priority": t.priority,
                "status": t.status,
                "issue": t.issue_description,
                "fault_type": t.fault_type,
                "recommended_action": t.recommended_action,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]


health_service = SensorHealthService()
