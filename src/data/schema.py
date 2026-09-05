from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import pandas as pd


@dataclass
class SensorSchema:
    """Schema configuration mapping logical weather sensor fields to actual dataset columns.

    Matches the AWS schema structure (station_id, timestamp, latitude, longitude,
    temperature, pressure, humidity, etc.).
    """
    temperature: str = "temperature"
    pressure: str = "pressure"
    humidity: str = "humidity"
    station_id: str = "station_id"
    timestamp: str = "timestamp"
    latitude: str = "latitude"
    longitude: str = "longitude"
    original_time: str = "original_time"
    year: str = "year"
    month: str = "month"
    day: str = "day"
    hour: str = "hour"
    day_of_year: str = "day_of_year"

    @property
    def required_sensor_columns(self) -> List[str]:
        return [self.temperature, self.pressure, self.humidity]

    @property
    def required_columns(self) -> List[str]:
        return self.required_sensor_columns

    @property
    def metadata_columns(self) -> List[str]:
        return [self.station_id, self.timestamp, self.latitude, self.longitude]


def validate_sensor_columns(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
) -> Tuple[bool, List[str]]:
    """Verify that a DataFrame contains the required sensor measurement columns.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame to validate.
    schema : SensorSchema, optional
        Schema definition. Defaults to standard SensorSchema().

    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, missing_columns)
        is_valid is True if all required sensor columns are present; False otherwise.
        missing_columns lists all required column names specified by the schema that are absent.
    """
    if schema is None:
        schema = SensorSchema()

    missing = [col for col in schema.required_sensor_columns if col not in df.columns]
    is_valid = len(missing) == 0
    return is_valid, missing
