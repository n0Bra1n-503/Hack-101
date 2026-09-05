"""API endpoints for weather reading ingestion and retrieval."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.reading import (
    ErrorResponse,
    ReadingCreate,
    ReadingCreateResponse,
    ReadingResponse,
)
from backend.app.services.ingestion_service import (
    DuplicateReadingError,
    create_reading,
    get_reading_by_id,
    get_readings_by_station,
)

router = APIRouter(tags=["Readings"])


@router.post(
    "/api/readings",
    response_model=ReadingCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a weather reading",
    description="Validate incoming weather observation and persist it immutably into the database.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Reading successfully validated and stored.",
            "model": ReadingCreateResponse,
        },
        status.HTTP_409_CONFLICT: {
            "description": "Duplicate reading_id detected.",
            "model": ErrorResponse,
        },
        422: {
            "description": "Malformed payload or validation error.",
        },
    },
)
def ingest_reading(
    reading_in: ReadingCreate,
    db: Session = Depends(get_db),
) -> ReadingCreateResponse:
    """Ingest, validate, and persist a new raw weather reading."""
    try:
        persisted = create_reading(reading_in, db)
        return ReadingCreateResponse(
            message="Reading accepted and stored",
            reading=ReadingResponse.model_validate(persisted),
        )
    except DuplicateReadingError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "duplicate_reading",
                "message": str(e),
            },
        )


@router.get(
    "/api/stations/{id}/readings",
    response_model=List[ReadingResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve stored readings for a station",
    description="Retrieve historical observations recorded for a specific automated weather station.",
    responses={
        status.HTTP_200_OK: {
            "description": "List of station observations ordered by timestamp.",
            "model": List[ReadingResponse],
        },
    },
)
def get_station_readings(
    id: str,
    start_time: Optional[datetime] = Query(None, description="Optional start timestamp filter (UTC)"),
    end_time: Optional[datetime] = Query(None, description="Optional end timestamp filter (UTC)"),
    limit: Optional[int] = Query(None, description="Optional maximum number of readings to return"),
    db: Session = Depends(get_db),
) -> List[ReadingResponse]:
    """Retrieve all readings for a station with optional time-range filtering."""
    readings = get_readings_by_station(
        station_id=id,
        db=db,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return [ReadingResponse.model_validate(r) for r in readings]


@router.get(
    "/api/readings/{reading_id}",
    response_model=ReadingResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single reading by identifier",
    description="Fetch an immutable raw observation record by reading_id.",
    responses={
        status.HTTP_200_OK: {
            "description": "The matching weather observation record.",
            "model": ReadingResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Reading not found.",
            "model": ErrorResponse,
        },
    },
)
def get_reading(
    reading_id: str,
    db: Session = Depends(get_db),
) -> ReadingResponse:
    """Retrieve an individual reading by reading_id."""
    reading = get_reading_by_id(reading_id, db)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "reading_not_found",
                "message": f"No reading found for reading_id '{reading_id}'",
            },
        )
    return ReadingResponse.model_validate(reading)
