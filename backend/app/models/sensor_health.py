"""SQLAlchemy model for station and sensor health (Digital Twin)."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from backend.app.database.connection import Base


class SensorHealth(Base):
    """Digital Twin health metrics for weather stations."""

    __tablename__ = "sensor_health"

    health_id = Column(String, primary_key=True, index=True, nullable=False)
    station_id = Column(String, unique=True, index=True, nullable=False)

    recent_health_score = Column(Float, nullable=False, default=100.0)  # 0 to 100
    historical_health_score = Column(Float, nullable=False, default=100.0)  # 0 to 100

    total_readings = Column(Integer, nullable=False, default=0)
    anomaly_count = Column(Integer, nullable=False, default=0)
    fault_count = Column(Integer, nullable=False, default=0)

    last_fault_type = Column(String, nullable=True)
    last_fault_timestamp = Column(DateTime, nullable=True)

    maintenance_priority = Column(String, nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    health_details = Column(Text, nullable=True)  # JSON-encoded metrics per channel

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SensorHealth(station_id='{self.station_id}', score={self.recent_health_score})>"
