"""SQLAlchemy model for disaster risks and public safety advisories."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Index, String, Text
from backend.app.database.connection import Base


class DisasterRisk(Base):
    """Disaster risk assessment derived strictly from validated genuine weather events."""

    __tablename__ = "risk_events"

    risk_id = Column(String, primary_key=True, index=True, nullable=False)
    area = Column(String, index=True, nullable=False)
    risk_level = Column(String, nullable=False)  # LOW, MEDIUM, HIGH
    event_type = Column(String, nullable=False)  # extreme_heat, flash_flood, storm_surge, heavy_rainfall, gale_winds

    confidence = Column(Float, nullable=False, default=0.8)
    trigger_reading_id = Column(String, nullable=True)
    supporting_stations = Column(Text, nullable=True)  # JSON-encoded list of station IDs confirming event

    public_message = Column(Text, nullable=False)
    safety_guidance = Column(Text, nullable=False)
    advisory_status = Column(String, nullable=False, default="monitoring")  # monitoring, advisory_active, none

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_risks_area_level", "area", "risk_level"),
    )

    def __repr__(self) -> str:
        return f"<DisasterRisk(id='{self.risk_id}', area='{self.area}', level='{self.risk_level}')>"
