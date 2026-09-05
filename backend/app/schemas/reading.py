"""Pydantic schemas for weather reading ingestion, validation, and responses."""

import hashlib
import math
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReadingBase(BaseModel):
    """Base schema containing canonical weather observation fields.

    All measurement channels and optional metadata support NULL to represent
    real-world automated weather station sensor realities (uninstalled channels,
    hardware dropouts, dry periods) without fabricating false values or 0s.
    """

    reading_id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the weather reading. If omitted during creation, generated deterministically server-side.",
        examples=["R123"],
    )
    station_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the reporting automated weather station",
        examples=["AWS-104"],
    )
    timestamp: datetime = Field(
        ...,
        description="Observation timestamp in ISO 8601 UTC format",
        examples=["2026-09-04T10:00:00"],
    )

    # Core measurement channels — Nullable to reflect real AWS sensor dropouts
    temperature: Optional[float] = Field(
        default=None,
        description="Ambient temperature in degrees Celsius (°C). Extreme values are structurally valid.",
        examples=[31.2],
    )
    pressure: Optional[float] = Field(
        default=None,
        description="Atmospheric barometric pressure in hectopascals (hPa)",
        examples=[1004.1],
    )
    humidity: Optional[float] = Field(
        default=None,
        description="Relative humidity percentage (0.0 to 100.0 %). Preserves raw values if corrupted.",
        examples=[48.2],
    )
    wind_speed: Optional[float] = Field(
        default=None,
        description="Wind speed in meters per second (m/s)",
        examples=[12.4],
    )
    wind_direction: Optional[float] = Field(
        default=None,
        description="Wind direction in degrees from true north (0.0 to 360.0°). NULL if channel unavailable.",
        examples=[220.0],
    )
    rainfall: Optional[float] = Field(
        default=None,
        description="Precipitation accumulation in millimeters (mm). NULL if dry/unequipped.",
        examples=[0.0],
    )
    solar_radiation: Optional[float] = Field(
        default=None,
        description="Solar irradiance in Watts per square meter (W/m²). NULL if channel unavailable.",
        examples=[650.0],
    )

    # Geographic metadata
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Latitude of the station in decimal degrees (-90.0 to 90.0)",
        examples=[28.61],
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Longitude of the station in decimal degrees (-180.0 to 180.0)",
        examples=[77.21],
    )
    area: Optional[str] = Field(
        default=None,
        description="Geographic or administrative area / district",
        examples=["Delhi"],
    )
    elevation: Optional[float] = Field(
        default=None,
        description="Station elevation above sea level in meters (altitude). NULL if unrecorded.",
        examples=[216.0],
    )

    # Provenance & Data Quality
    source: str = Field(
        default="weather_source",
        min_length=1,
        description="Origin of telemetry stream (e.g. 'IMD_AWS', 'weather_source')",
        examples=["weather_source"],
    )
    quality_flag: str = Field(
        default="valid",
        min_length=1,
        description="Structural data quality indicator ('valid', 'missing', 'malformed', 'duplicate')",
        examples=["valid"],
    )

    @model_validator(mode="before")
    @classmethod
    def map_raw_field_aliases(cls, data: Any) -> Any:
        """Map raw source field names to canonical SkyGuard schema names and convert NaN to None."""
        if isinstance(data, dict):
            data = data.copy()
            if "relative_humidity" in data and "humidity" not in data:
                data["humidity"] = data.pop("relative_humidity")
            if "atmospheric_pressure" in data and "pressure" not in data:
                data["pressure"] = data.pop("atmospheric_pressure")
            if "altitude" in data and "elevation" not in data:
                data["elevation"] = data.pop("altitude")

            # Strictly convert any NaN float values to None (representing SQL NULL)
            for k, v in list(data.items()):
                if isinstance(v, float) and math.isnan(v):
                    data[k] = None
        return data


class ReadingCreate(ReadingBase):
    """Schema for incoming reading ingestion payload."""

    pass


class ReadingResponse(ReadingBase):
    """Schema for serialized weather reading responses.

    Guarantees that reading_id is always present in persistent API responses.
    """

    reading_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the persisted weather reading",
        examples=["R123"],
    )

    model_config = ConfigDict(from_attributes=True)


class ReadingCreateResponse(BaseModel):
    """Response returned upon successful ingestion and persistence."""

    message: str = Field(
        default="Reading accepted and stored",
        description="Operational status message",
    )
    reading: ReadingResponse = Field(
        ...,
        description="The persisted weather observation record",
    )


class ErrorResponse(BaseModel):
    """Structured error response schema for API failures."""

    error: str = Field(..., description="Error category code", examples=["duplicate_reading"])
    message: str = Field(..., description="Human-readable explanation of the error", examples=["Reading with reading_id 'R123' already exists"])
    details: Optional[Any] = Field(default=None, description="Optional diagnostic details")
