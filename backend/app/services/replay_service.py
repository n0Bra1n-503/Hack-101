"""Historical Telemetry Replay Engine.

Replays actual historical weather observations from the database through the full
pipeline (ML -> Decision Intelligence -> Trust -> Health -> Risk) and streams
live event updates over WebSockets.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.database.session import SessionLocal
from backend.app.models.reading import Reading
from backend.app.services.ml_service import get_ml_service
from backend.app.services.decision_service import decision_service
from backend.app.services.health_service import health_service
from backend.app.services.risk_service import risk_service
from backend.app.websocket.manager import ws_manager

logger = logging.getLogger("skyguard.replay")


class ReplayEngine:
    """Historical telemetry streaming and replay controller."""

    def __init__(self):
        self.state = "STOPPED"  # STOPPED, PLAYING, PAUSED
        self.speed = 1.0
        self.current_index = 0
        self.station_id: Optional[str] = None
        self._task: Optional[asyncio.Task] = None
        self._replay_readings: List[Dict[str, Any]] = []

    def start(self, station_id: Optional[str] = None, speed: float = 1.0) -> Dict[str, Any]:
        """Start or restart historical replay."""
        self.reset()
        self.station_id = station_id
        self.speed = max(0.1, min(10.0, speed))
        self.state = "PLAYING"

        # Load historical batch from DB
        db = SessionLocal()
        try:
            q = db.query(Reading)
            if station_id:
                q = q.filter(Reading.station_id == station_id)
            readings = q.order_by(Reading.timestamp.asc()).limit(500).all()
            self._replay_readings = [
                {
                    "reading_id": r.reading_id,
                    "station_id": r.station_id,
                    "timestamp": r.timestamp.isoformat(),
                    "temperature": r.temperature,
                    "pressure": r.pressure,
                    "humidity": r.humidity,
                    "wind_speed": r.wind_speed,
                    "rainfall": r.rainfall,
                    "area": r.area,
                }
                for r in readings
            ]
        finally:
            db.close()

        logger.info(f"Replay started: {len(self._replay_readings)} records queued at {self.speed}x speed.")
        self._task = asyncio.create_task(self._playback_loop())
        return self.get_status()

    def pause(self) -> Dict[str, Any]:
        if self.state == "PLAYING":
            self.state = "PAUSED"
            logger.info("Replay paused.")
        return self.get_status()

    def resume(self) -> Dict[str, Any]:
        if self.state == "PAUSED":
            self.state = "PLAYING"
            logger.info("Replay resumed.")
        return self.get_status()

    def reset(self) -> Dict[str, Any]:
        self.state = "STOPPED"
        self.current_index = 0
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None
        logger.info("Replay reset.")
        return self.get_status()

    def set_speed(self, speed: float) -> Dict[str, Any]:
        self.speed = max(0.1, min(10.0, speed))
        logger.info(f"Replay speed adjusted to {self.speed}x.")
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "speed": self.speed,
            "current_index": self.current_index,
            "total_records": len(self._replay_readings),
            "station_id": self.station_id,
        }

    async def _playback_loop(self):
        """Streaming playback worker."""
        ml_svc = get_ml_service()
        while self.current_index < len(self._replay_readings) and self.state != "STOPPED":
            if self.state == "PAUSED":
                await asyncio.sleep(0.5)
                continue

            obs = self._replay_readings[self.current_index]
            self.current_index += 1

            # Process observation through pipeline
            db = SessionLocal()
            try:
                ml_res = ml_svc.detect_anomaly(obs)
                dec_res = decision_service.evaluate_reading(obs, ml_res, db)
                health_service.record_observation_health(obs["station_id"], dec_res, db)
                risk_rec = risk_service.evaluate_weather_risk(obs, dec_res, db)

                # Broadcast live updates to connected frontends
                await ws_manager.broadcast("reading", obs)
                await ws_manager.broadcast("trust_update", {
                    "station_id": obs["station_id"],
                    "trust_score": dec_res["trust_score"],
                    "decision": dec_res["decision"],
                })
                if dec_res["decision"] == "sensor_fault":
                    await ws_manager.broadcast("anomaly", dec_res)
                if risk_rec:
                    await ws_manager.broadcast("risk_update", {
                        "area": risk_rec.area,
                        "risk_level": risk_rec.risk_level,
                        "event_type": risk_rec.event_type,
                    })

            except Exception as e:
                logger.error(f"Error in replay step: {e}")
            finally:
                db.close()

            # Delay proportional to speed
            delay = max(0.05, 1.0 / self.speed)
            await asyncio.sleep(delay)

        self.state = "STOPPED"
        logger.info("Replay stream reached end of dataset.")


replay_engine = ReplayEngine()
