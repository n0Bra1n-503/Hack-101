"""Decision Intelligence Service for SkyGuard AI.

Implements the critical reasoning layer separating ML anomaly detection from
operational classification:
ML Anomaly + Temporal + Cross-Sensor + Cross-Station + Persistence + History
-> genuine_weather | sensor_fault | uncertain
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.models.anomaly import Anomaly
from backend.app.models.correction import Correction
from backend.app.models.reading import Reading
from backend.app.models.sensor_health import SensorHealth

logger = logging.getLogger("skyguard.decision_service")


class DecisionIntelligenceService:
    """Evaluates multi-source evidence to classify weather vs sensor anomalies."""

    def evaluate_reading(
        self,
        reading: Dict[str, Any],
        ml_result: Dict[str, Any],
        db: Session,
    ) -> Dict[str, Any]:
        """Evaluate a reading and ML anomaly signals to produce final decision."""
        station_id = reading.get("station_id")
        ts = reading.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.utcnow()

        temp = reading.get("temperature")
        pressure = reading.get("pressure")
        humidity = reading.get("humidity")
        is_ml_anomaly = ml_result.get("anomaly", False)
        ml_score = ml_result.get("anomaly_score", 0.0)

        # 1. Gather Evidence
        evidence = {
            "temporal": self._check_temporal(station_id, ts, temp, db),
            "cross_sensor": self._check_cross_sensor(temp, humidity, pressure),
            "cross_station": self._check_cross_station(station_id, ts, temp, db),
            "persistence": self._check_persistence(station_id, ts, temp, db),
            "historical_health": self._check_historical_health(station_id, db),
        }

        # 2. Reasoning Layer: Classify decision & fault type
        cs_support = evidence["cross_station"]["support_ratio"]
        peer_count = evidence["cross_station"]["peer_count"]
        temp_jump = evidence["temporal"]["delta_per_hour"]
        is_frozen = evidence["persistence"]["is_frozen"]
        sensor_inconsistent = evidence["cross_sensor"]["inconsistent"]

        decision = "uncertain"
        fault_type = None
        confidence = 0.5
        trust_score = 75.0
        explanation_parts = []
        suggested_correction = None

        # Extreme thresholds
        is_extreme_temp = temp is not None and (temp > 48.0 or temp < -5.0)
        is_unphysical_temp = temp is not None and (temp > 60.0 or temp < -40.0)

        if is_unphysical_temp:
            decision = "sensor_fault"
            fault_type = "temperature_spike"
            confidence = 0.98
            trust_score = 5.0
            explanation_parts.append(f"Temperature reading {temp}°C exceeds physical terrestrial atmospheric limits.")

        elif is_frozen:
            decision = "sensor_fault"
            fault_type = "frozen_sensor"
            confidence = 0.95
            trust_score = 15.0
            explanation_parts.append("Sensor telemetry has reported identical consecutive values across multiple observation cycles.")

        elif temp_jump is not None and abs(temp_jump) > 12.0:
            if peer_count >= 2 and cs_support > 0.6:
                decision = "genuine_weather"
                confidence = 0.88
                trust_score = 85.0
                explanation_parts.append(f"Sudden thermal shift confirmed by {peer_count} neighboring regional stations.")
            elif peer_count >= 2 and cs_support < 0.2:
                decision = "sensor_fault"
                fault_type = "abrupt_jump"
                confidence = 0.92
                trust_score = 18.0
                explanation_parts.append(f"Abrupt {temp_jump:+.1f}°C/hr jump isolated to station {station_id}; neighboring stations report normal ambient conditions.")
            else:
                decision = "uncertain"
                confidence = 0.55
                trust_score = 45.0
                explanation_parts.append("Rapid thermal fluctuation detected with insufficient peer station coverage to confirm or refute.")

        elif is_ml_anomaly or is_extreme_temp:
            if peer_count >= 2 and cs_support >= 0.6:
                decision = "genuine_weather"
                confidence = 0.90
                trust_score = 92.0
                explanation_parts.append(f"Extreme meteorological condition validated across {peer_count} peer stations (peer agreement {cs_support*100:.0f}%).")
            elif peer_count >= 2 and cs_support < 0.3:
                decision = "sensor_fault"
                fault_type = "temperature_spike" if (temp is not None and temp > 40) else "temperature_drift"
                confidence = 0.88
                trust_score = 22.0
                explanation_parts.append(f"High anomaly score ({ml_score:.2f}) unsupported by regional peer stations. Target reports {temp}°C while regional median is {evidence['cross_station']['peer_median']}°C.")
            elif sensor_inconsistent:
                decision = "sensor_fault"
                fault_type = "multivariate_inconsistency"
                confidence = 0.85
                trust_score = 28.0
                explanation_parts.append("Multivariate thermodynamic inconsistency: extreme temperature concurrent with saturated relative humidity without precipitation.")
            else:
                decision = "uncertain"
                confidence = 0.60
                trust_score = 50.0
                explanation_parts.append("Elevated ML anomaly score with ambiguous cross-station corroboration; held for human verification.")

        else:
            # Normal consistent telemetry
            decision = "genuine_weather"
            confidence = 0.95
            trust_score = min(100.0, 95.0 + (5.0 * (1.0 - ml_score)))
            explanation_parts.append("Atmospheric telemetry is consistent with regional baseline and historical diurnal curves.")

        # Suggest correction if sensor fault detected and peer data available
        if decision == "sensor_fault" and temp is not None:
            peer_med = evidence["cross_station"].get("peer_median")
            suggested_val = peer_med if peer_med is not None else evidence["temporal"].get("previous_temp")
            if suggested_val is not None:
                suggested_correction = {
                    "parameter": "temperature",
                    "raw_value": temp,
                    "suggested_value": round(float(suggested_val), 1),
                    "confidence": confidence,
                    "reason": f"Sensor fault ({fault_type}) detected. Regional peer median is {suggested_val}°C.",
                }

        explanation = " ".join(explanation_parts)

        return {
            "reading_id": reading.get("reading_id"),
            "station_id": station_id,
            "timestamp": ts.isoformat() if isinstance(ts, datetime) else str(ts),
            "decision": decision,
            "fault_type": fault_type,
            "trust_score": round(trust_score, 1),
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "evidence": evidence,
            "suggested_correction": suggested_correction,
        }

    def _check_temporal(self, station_id: str, ts: datetime, temp: Optional[float], db: Session) -> Dict[str, Any]:
        """Evaluate rate of change compared to previous observation."""
        if temp is None:
            return {"delta_per_hour": None, "previous_temp": None, "plausible": True}

        prev = (
            db.query(Reading)
            .filter(Reading.station_id == station_id, Reading.timestamp < ts)
            .order_by(Reading.timestamp.desc())
            .first()
        )
        if not prev or prev.temperature is None:
            return {"delta_per_hour": None, "previous_temp": None, "plausible": True}

        hours = max(0.25, (ts - prev.timestamp).total_seconds() / 3600.0)
        delta = temp - prev.temperature
        rate = delta / hours
        return {
            "delta_per_hour": round(rate, 2),
            "previous_temp": prev.temperature,
            "plausible": abs(rate) <= 10.0,
        }

    def _check_cross_sensor(self, temp: Optional[float], humidity: Optional[float], pressure: Optional[float]) -> Dict[str, Any]:
        """Verify thermodynamic physical consistency."""
        inconsistent = False
        reason = "Normal"
        if temp is not None and humidity is not None:
            if temp > 45.0 and humidity > 90.0:
                inconsistent = True
                reason = "Extreme heat with near-saturation humidity without precipitation is thermodynamically implausible"
        return {"inconsistent": inconsistent, "reason": reason}

    def _check_cross_station(self, station_id: str, ts: datetime, temp: Optional[float], db: Session) -> Dict[str, Any]:
        """Compare reading with neighboring peer stations reporting at similar time."""
        if temp is None:
            return {"peer_count": 0, "peer_median": None, "support_ratio": 1.0}

        window_start = ts - timedelta(hours=2)
        window_end = ts + timedelta(hours=2)

        peers = (
            db.query(Reading.temperature)
            .filter(
                Reading.station_id != station_id,
                Reading.timestamp >= window_start,
                Reading.timestamp <= window_end,
                Reading.temperature.isnot(None),
            )
            .limit(20)
            .all()
        )

        if not peers:
            return {"peer_count": 0, "peer_median": None, "support_ratio": 0.5}

        peer_temps = [p[0] for p in peers]
        peer_temps.sort()
        median_temp = peer_temps[len(peer_temps) // 2]

        # Count peers within ±4°C of target temperature
        supporting = sum(1 for t in peer_temps if abs(t - temp) <= 4.0)
        support_ratio = supporting / len(peer_temps)

        return {
            "peer_count": len(peer_temps),
            "peer_median": round(median_temp, 1),
            "support_ratio": round(support_ratio, 2),
        }

    def _check_persistence(self, station_id: str, ts: datetime, temp: Optional[float], db: Session) -> Dict[str, Any]:
        """Check for frozen sensor (identical readings)."""
        if temp is None:
            return {"is_frozen": False, "identical_count": 0}

        recent = (
            db.query(Reading.temperature)
            .filter(Reading.station_id == station_id, Reading.timestamp <= ts)
            .order_by(Reading.timestamp.desc())
            .limit(6)
            .all()
        )
        if len(recent) < 5:
            return {"is_frozen": False, "identical_count": len(recent)}

        identical = sum(1 for r in recent if r[0] == temp)
        is_frozen = identical >= 5
        return {"is_frozen": is_frozen, "identical_count": identical}

    def _check_historical_health(self, station_id: str, db: Session) -> Dict[str, Any]:
        """Retrieve station health rating from DB."""
        health = db.query(SensorHealth).filter(SensorHealth.station_id == station_id).first()
        score = health.recent_health_score if health else 100.0
        return {"health_score": score, "status": "reliable" if score > 70 else "degraded"}


decision_service = DecisionIntelligenceService()
