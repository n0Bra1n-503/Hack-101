"""SQLAlchemy model for anomaly detections and decision intelligence outputs."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Index, String, Text
from backend.app.database.connection import Base


class Anomaly(Base):
    """Anomaly detection results and decision intelligence records."""

    __tablename__ = "anomalies"

    anomaly_id = Column(String, primary_key=True, index=True, nullable=False)
    reading_id = Column(String, index=True, nullable=False)
    station_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)

    is_anomaly = Column(Boolean, nullable=False, default=False)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    model_name = Column(String, nullable=False, default="hybrid")

    statistical_score = Column(Float, nullable=False, default=0.0)
    isolation_forest_score = Column(Float, nullable=False, default=0.0)
    autoencoder_score = Column(Float, nullable=False, default=0.0)

    # Decision Intelligence output
    decision = Column(String, nullable=False, default="uncertain")  # genuine_weather, sensor_fault, uncertain
    fault_type = Column(String, nullable=True)  # temperature_spike, frozen_sensor, etc.
    trust_score = Column(Float, nullable=False, default=100.0)  # 0 to 100
    confidence = Column(Float, nullable=False, default=0.5)
    explanation = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)  # JSON-encoded evidence dictionary

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_anomalies_station_timestamp", "station_id", "timestamp"),
        Index("ix_anomalies_decision", "decision"),
    )

    def __repr__(self) -> str:
        return f"<Anomaly(anomaly_id='{self.anomaly_id}', station_id='{self.station_id}', decision='{self.decision}')>"
