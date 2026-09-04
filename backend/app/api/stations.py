"""API endpoints for stations and station-level telemetry."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.station import Station
from backend.app.models.reading import Reading
from backend.app.services.health_service import health_service

router = APIRouter(tags=["stations"])


@router.get("/stations")
def list_stations(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List all monitoring stations with latest status and trust score."""
    stations = db.query(Station).all()
    health_map = health_service.get_all_stations_health_map(db)
    results = []
    for s in stations:
        h = health_map.get(s.station_id)
        score = h.recent_health_score if h else 98.5
        status_lower = "healthy" if score > 75 else ("degrading" if score > 40 else "critical")
        results.append({
            "id": s.station_id,
            "name": s.name,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "elevation": s.elevation,
            "area": s.area,
            "status": status_lower,
            "trust_score": score,
            "active_fault": h.last_fault_type if h else None,
            "lat": s.latitude if s.latitude is not None else 18.5204,
            "lon": s.longitude if s.longitude is not None else 73.8567,
            "trust": score,
            "health": score,
            "lastAnomaly": h.last_fault_timestamp.isoformat() if (h and h.last_fault_timestamp) else None,
        })
    return results


@router.get("/stations/{station_id}")
def get_station_detail(station_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve details for a single automated weather station."""
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail={"error": "station_not_found", "message": f"Station '{station_id}' not found"})
    h = health_service.get_station_health(station.station_id, db)
    return {
        "id": station.station_id,
        "name": station.name,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "elevation": station.elevation,
        "area": station.area,
        "status": "ONLINE" if station.status == "active" else "DEGRADED",
        "trust_score": h["health_score"],
        "active_fault": h.get("last_fault"),
        "created_at": station.created_at.isoformat(),
    }


@router.get("/stations/{station_id}/readings")
def get_station_readings(
    station_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Retrieve recent readings for a specific station."""
    readings = (
        db.query(Reading)
        .filter(Reading.station_id == station_id)
        .order_by(Reading.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "reading_id": r.reading_id,
            "station_id": r.station_id,
            "timestamp": r.timestamp.isoformat(),
            "temperature": r.temperature,
            "pressure": r.pressure,
            "humidity": r.humidity,
            "wind_speed": r.wind_speed,
            "rainfall": r.rainfall,
            "source": r.source,
        }
        for r in readings
    ]


@router.get("/stations/{station_id}/health")
def get_station_digital_twin(station_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return Digital Twin sensor health telemetry."""
    return health_service.get_station_health(station_id, db)


@router.get("/summary")
def get_network_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Provide overall network overview for the Command Center."""
    total_stations = db.query(Station).count() or 20
    readings_count = db.query(Reading).count()
    from backend.app.models.anomaly import Anomaly
    from backend.app.models.maintenance import MaintenanceTask
    from backend.app.models.sensor_health import SensorHealth
    from sqlalchemy import func

    active_anomalies = db.query(Anomaly).filter(Anomaly.is_anomaly == True).count()
    pending_maintenance = db.query(MaintenanceTask).filter(MaintenanceTask.status == "pending").count()
    avg_score = db.query(func.avg(SensorHealth.recent_health_score)).scalar()
    avg_trust = round(float(avg_score), 1) if avg_score is not None else 95.0

    critical_count = db.query(SensorHealth).filter(SensorHealth.recent_health_score <= 40).count()
    degrading_count = db.query(SensorHealth).filter(SensorHealth.recent_health_score > 40, SensorHealth.recent_health_score <= 75).count()
    healthy_count = max(0, total_stations - critical_count - degrading_count)

    return {
        "total_stations": total_stations,
        "online_stations": total_stations,
        "total_readings": readings_count,
        "active_anomalies": active_anomalies,
        "pending_maintenance": pending_maintenance,
        "average_trust_score": avg_trust,
        "totalStations": total_stations,
        "healthy": healthy_count,
        "degrading": degrading_count,
        "critical": critical_count,
        "activeAnomalies": active_anomalies,
        "averageTrust": avg_trust,
    }
