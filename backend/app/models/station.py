"""SQLAlchemy model for weather stations."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, String
from backend.app.database.connection import Base


class Station(Base):
    """Weather Station metadata."""

    __tablename__ = "stations"

    station_id = Column(String, primary_key=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)
    area = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Station(station_id='{self.station_id}', name='{self.name}', area='{self.area}')>"
