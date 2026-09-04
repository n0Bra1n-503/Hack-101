"""SQLAlchemy model for predictive maintenance queue."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Index, String, Text
from backend.app.database.connection import Base


class MaintenanceTask(Base):
    """Predictive maintenance queue item."""

    __tablename__ = "maintenance_queue"

    maintenance_id = Column(String, primary_key=True, index=True, nullable=False)
    station_id = Column(String, index=True, nullable=False)
    priority = Column(String, nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, nullable=False, default="pending")  # pending, in_progress, resolved

    issue_description = Column(Text, nullable=False)
    fault_type = Column(String, nullable=False)
    recommended_action = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_maintenance_station_status", "station_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<MaintenanceTask(id='{self.maintenance_id}', station='{self.station_id}', priority='{self.priority}')>"
