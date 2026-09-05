"""SQLAlchemy model for data corrections."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Index, String, Text
from backend.app.database.connection import Base


class Correction(Base):
    """Suggested data correction requiring human review and approval."""

    __tablename__ = "corrections"

    correction_id = Column(String, primary_key=True, index=True, nullable=False)
    reading_id = Column(String, index=True, nullable=False)
    station_id = Column(String, index=True, nullable=False)
    parameter = Column(String, nullable=False)  # temperature, humidity, etc.

    raw_value = Column(Float, nullable=True)
    suggested_value = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False, default=0.8)
    reason = Column(Text, nullable=False)

    review_status = Column(String, nullable=False, default="pending")  # pending, accepted, rejected, reviewed
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_corrections_station_status", "station_id", "review_status"),
    )

    def __repr__(self) -> str:
        return f"<Correction(correction_id='{self.correction_id}', status='{self.review_status}')>"
