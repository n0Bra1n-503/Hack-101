"""API endpoints for anomaly investigations and real-time ML inference."""

from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.anomaly import Anomaly
from backend.app.models.reading import Reading
from backend.app.models.correction import Correction
from backend.app.services.ml_service import get_ml_service
from backend.app.services.decision_service import decision_service
from backend.app.services.health_service import health_service
from backend.app.services.risk_service import risk_service

router = APIRouter(tags=["anomalies", "inference"])


@router.get("/anomalies")
def list_anomalies(limit: int = 50, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List recent detected anomalies and decision intelligence outputs."""
    anomalies = db.query(Anomaly).order_by(Anomaly.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.anomaly_id,
            "reading_id": a.reading_id,
            "station_id": a.station_id,
            "timestamp": a.timestamp.isoformat(),
            "anomaly_score": a.anomaly_score,
            "decision": a.decision,
            "fault_type": a.fault_type,
            "trust_score": a.trust_score,
            "confidence": a.confidence,
            "explanation": a.explanation,
        }
        for a in anomalies
    ]


@router.get("/anomalies/{anomaly_id}")
def get_anomaly_detail(anomaly_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve detailed investigation dossier for a specific anomaly."""
    anomaly = db.query(Anomaly).filter(Anomaly.anomaly_id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail={"error": "anomaly_not_found", "message": f"Anomaly '{anomaly_id}' not found"})

    reading = db.query(Reading).filter(Reading.reading_id == anomaly.reading_id).first()
    correction = db.query(Correction).filter(Correction.reading_id == anomaly.reading_id).first()

    return {
        "id": anomaly.anomaly_id,
        "reading_id": anomaly.reading_id,
        "station_id": anomaly.station_id,
        "timestamp": anomaly.timestamp.isoformat(),
        "is_anomaly": anomaly.is_anomaly,
        "anomaly_score": anomaly.anomaly_score,
        "model": anomaly.model_name,
        "signals": {
            "statistical": anomaly.statistical_score,
            "isolation_forest": anomaly.isolation_forest_score,
            "autoencoder": anomaly.autoencoder_score,
        },
        "decision": anomaly.decision,
        "fault_type": anomaly.fault_type,
        "trust_score": anomaly.trust_score,
        "confidence": anomaly.confidence,
        "explanation": anomaly.explanation,
        "reading": {
            "temperature": reading.temperature if reading else None,
            "pressure": reading.pressure if reading else None,
            "humidity": reading.humidity if reading else None,
            "wind_speed": reading.wind_speed if reading else None,
        } if reading else None,
        "suggested_correction": {
            "parameter": correction.parameter,
            "raw_value": correction.raw_value,
            "suggested_value": correction.suggested_value,
            "status": correction.review_status,
        } if correction else None,
    }


@router.post("/inference")
def run_full_inference(
    observation: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Execute end-to-end SkyGuard AI pipeline for a weather observation:

    Telemetry -> ML Anomaly Models -> Decision Intelligence -> Trust Score -> Health -> Risk
    """
    # 1. Run ML Anomaly Detection (Manan trained models)
    ml_svc = get_ml_service()
    ml_output = ml_svc.detect_anomaly(observation)

    # 2. Run Decision Intelligence (Mitali reasoning layer)
    dec_output = decision_service.evaluate_reading(observation, ml_output, db)

    # 3. Persist Anomaly / Decision Record
    now = datetime.utcnow()
    rid = observation.get("reading_id") or f"INF-{int(now.timestamp() * 1000)}"
    aid = f"ANOM-{rid[:16]}"

    anomaly_rec = Anomaly(
        anomaly_id=aid,
        reading_id=rid,
        station_id=observation.get("station_id", "UNKNOWN"),
        timestamp=observation.get("timestamp") if isinstance(observation.get("timestamp"), datetime) else now,
        is_anomaly=ml_output.get("anomaly", False),
        anomaly_score=ml_output.get("anomaly_score", 0.0),
        model_name=ml_output.get("model", "hybrid"),
        statistical_score=ml_output.get("signals", {}).get("statistical", 0.0),
        isolation_forest_score=ml_output.get("signals", {}).get("isolation_forest", 0.0),
        autoencoder_score=ml_output.get("signals", {}).get("autoencoder", 0.0),
        decision=dec_output.get("decision", "uncertain"),
        fault_type=dec_output.get("fault_type"),
        trust_score=dec_output.get("trust_score", 100.0),
        confidence=dec_output.get("confidence", 0.8),
        explanation=dec_output.get("explanation"),
        created_at=now,
    )
    db.add(anomaly_rec)

    # 4. Handle suggested correction
    corr = dec_output.get("suggested_correction")
    if corr:
        corr_rec = Correction(
            correction_id=f"CORR-{rid[:16]}",
            reading_id=rid,
            station_id=observation.get("station_id", "UNKNOWN"),
            parameter=corr["parameter"],
            raw_value=corr["raw_value"],
            suggested_value=corr["suggested_value"],
            confidence=corr["confidence"],
            reason=corr["reason"],
            review_status="pending",
            timestamp=now,
            created_at=now,
        )
        db.add(corr_rec)

    db.commit()

    # 5. Update Digital Twin Health
    health_service.record_observation_health(observation.get("station_id", "UNKNOWN"), dec_output, db)

    # 6. Assess Disaster Risk (Only genuine weather is permitted to proceed)
    risk_rec = risk_service.evaluate_weather_risk(observation, dec_output, db)

    return {
        "status": "success",
        "reading_id": rid,
        "anomaly_detection": ml_output,
        "decision_intelligence": dec_output,
        "disaster_risk": {
            "risk_id": risk_rec.risk_id,
            "risk_level": risk_rec.risk_level,
            "event_type": risk_rec.event_type,
            "public_message": risk_rec.public_message,
        } if risk_rec else {
            "risk_level": "NONE",
            "status": "BLOCKED_OR_NOMINAL",
        },
    }
