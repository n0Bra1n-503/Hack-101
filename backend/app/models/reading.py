"""SQLAlchemy ORM model for raw, immutable weather readings."""

from sqlalchemy import Column, DateTime, Float, Index, String
from backend.app.database.connection import Base


class Reading(Base):
    """Raw, immutable weather observation telemetry record."""

    __tablename__ = "readings"

    reading_id = Column(String, primary_key=True, index=True, nullable=False)
    station_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)

    temperature = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    solar_radiation = Column(Float, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area = Column(String, nullable=True)
    elevation = Column(Float, nullable=True)

    source = Column(String, nullable=False, default="weather_source")
    quality_flag = Column(String, nullable=False, default="valid")

    __table_args__ = (
        Index("ix_readings_station_timestamp", "station_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Reading(reading_id='{self.reading_id}', station_id='{self.station_id}', timestamp='{self.timestamp}')>"
