"""Ingestion service for validated weather readings and database persistence."""

import hashlib
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.reading import Reading
from backend.app.schemas.reading import ReadingCreate

logger = logging.getLogger("skyguard.ingestion")


class DuplicateReadingError(Exception):
    """Raised when an ingested reading_id or physical observation already exists."""

    def __init__(self, reading_id: str):
        self.reading_id = reading_id
        super().__init__(f"Reading with reading_id '{reading_id}' already exists")


class ReadingNotFoundError(Exception):
    """Raised when a requested reading cannot be found."""

    def __init__(self, reading_id: str):
        self.reading_id = reading_id
        super().__init__(f"No reading found for reading_id '{reading_id}'")


def disambiguate_station_id(
    station_id: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """Disambiguate physical station identifier when multiple physical sites share the same name.

    Specifically handles the two physically distinct 'Bhadar dam' stations in Gujarat:
      - Dam Site 1 (Rajkot district): Lat ~21.8100, Lon ~70.7689 -> 'Bhadar_Dam_Rajkot'
      - Dam Site 2 (Aravalli district): Lat ~23.3250, Lon ~73.6917 -> 'Bhadar_Dam_Aravalli'
    Preserves original name for all other stations or when coordinates are unavailable.
    """
    if station_id == "Bhadar dam" and latitude is not None:
        if abs(latitude - 21.81) < 0.3:
            return "Bhadar_Dam_Rajkot"
        elif abs(latitude - 23.325) < 0.3:
            return "Bhadar_Dam_Aravalli"
    return station_id


def generate_reading_id(
    station_id: str,
    timestamp: datetime | str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """Generate a deterministic, collision-safe 24-character SHA-256 reading identifier.

    Guarantees that two physical stations sharing a station name (such as the two
    distinct Bhadar dam reservoirs in Gujarat) produce completely distinct IDs.
    """
    physical_id = disambiguate_station_id(station_id, latitude, longitude)
    ts_str = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
    raw_key = f"{physical_id}_{ts_str}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]


def create_reading(reading_in: ReadingCreate, db: Session) -> Reading:
    """Validate and persist a new immutable weather reading.

    Parameters:
        reading_in: Validated Pydantic schema representing incoming observation.
        db: Active SQLAlchemy database session.

    Returns:
        The persisted SQLAlchemy Reading model instance.

    Raises:
        DuplicateReadingError: If a reading with the same reading_id or physical
                              (station_id, timestamp) already exists.
    """
    reading_dict = reading_in.model_dump()

    # Disambiguate physical station identifier if ambiguous
    physical_station_id = disambiguate_station_id(
        reading_in.station_id, reading_in.latitude, reading_in.longitude
    )
    reading_dict["station_id"] = physical_station_id

    # Deterministically generate reading_id if not supplied by caller
    if not reading_dict.get("reading_id"):
        reading_dict["reading_id"] = generate_reading_id(
            physical_station_id, reading_in.timestamp, reading_in.latitude, reading_in.longitude
        )

    reading_id = reading_dict["reading_id"]
    logger.info(f"Processing ingestion for reading_id={reading_id}, station_id={physical_station_id}")

    # Check for existing reading_id duplicate
    existing = db.query(Reading).filter(Reading.reading_id == reading_id).first()
    if existing:
        logger.warning(f"Duplicate reading detected by ID: reading_id={reading_id}")
        raise DuplicateReadingError(reading_id)

    # Check for existing physical (station_id, timestamp) duplicate
    existing_st_ts = (
        db.query(Reading)
        .filter(
            Reading.station_id == physical_station_id,
            Reading.timestamp == reading_in.timestamp,
        )
        .first()
    )
    if existing_st_ts:
        logger.warning(
            f"Duplicate physical observation detected: station={physical_station_id}, timestamp={reading_in.timestamp}"
        )
        raise DuplicateReadingError(existing_st_ts.reading_id)

    db_reading = Reading(**reading_dict)
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)

    logger.info(f"Reading successfully stored: reading_id={db_reading.reading_id}, station_id={db_reading.station_id}")
    return db_reading


def get_readings_by_station(
    station_id: str,
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[Reading]:
    """Retrieve historical stored readings for a given station with optional time-range filtering.

    Parameters:
        station_id: Identifier of the automated weather station.
        db: Active SQLAlchemy database session.
        start_time: Optional UTC ISO start timestamp.
        end_time: Optional UTC ISO end timestamp.

    Returns:
        List of matching SQLAlchemy Reading model instances.
    """
    # Support querying both raw umbrella name and disambiguated physical stations
    if station_id == "Bhadar dam":
        query = db.query(Reading).filter(
            (Reading.station_id == "Bhadar dam") | (Reading.station_id.like("Bhadar_Dam_%"))
        )
    else:
        query = db.query(Reading).filter(Reading.station_id == station_id)

    if start_time:
        query = query.filter(Reading.timestamp >= start_time)
    if end_time:
        query = query.filter(Reading.timestamp <= end_time)

    return query.order_by(Reading.timestamp.asc()).all()


def get_reading_by_id(reading_id: str, db: Session) -> Optional[Reading]:
    """Retrieve a single stored reading by its reading_id.

    Parameters:
        reading_id: Unique observation identifier.
        db: Active SQLAlchemy database session.

    Returns:
        SQLAlchemy Reading instance if found, or None.
    """
    return db.query(Reading).filter(Reading.reading_id == reading_id).first()
