from pathlib import Path
from typing import Union, Optional, List
import pandas as pd
from .schema import SensorSchema


def load_sensor_data(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """Load Automatic Weather Station sensor data from a CSV file.

    Parameters
    ----------
    path : Union[str, Path]
        Path to the CSV file or directory containing sensor files.
    **kwargs :
        Additional keyword arguments passed directly to pd.read_csv.

    Returns
    -------
    pd.DataFrame
        Loaded sensor data as a Pandas DataFrame.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the path is not a file or has an invalid format.
    """
    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Sensor data file/path not found at: {csv_path}")

    if csv_path.is_dir():
        # If directory passed, load merged dataset from directory
        return load_merged_sensor_data(data_dir=csv_path, **kwargs)

    if not csv_path.is_file():
        raise ValueError(f"Path exists but is not a file: {csv_path}")

    return pd.read_csv(csv_path, **kwargs)


def load_merged_sensor_data(
    temperature_path: Optional[Union[str, Path]] = None,
    pressure_path: Optional[Union[str, Path]] = None,
    humidity_path: Optional[Union[str, Path]] = None,
    data_dir: Optional[Union[str, Path]] = None,
    schema: Optional[SensorSchema] = None,
    **kwargs,
) -> pd.DataFrame:
    """Load and merge sensor data from 3 separate CSV files (temperature, pressure, humidity).

    Parameters
    ----------
    temperature_path : Optional[Union[str, Path]]
        Path to temperature CSV.
    pressure_path : Optional[Union[str, Path]]
        Path to pressure CSV.
    humidity_path : Optional[Union[str, Path]]
        Path to humidity CSV.
    data_dir : Optional[Union[str, Path]]
        Directory containing temperature.csv, pressure.csv, and humidity.csv.
    schema : Optional[SensorSchema]
        Schema instance specifying column names.
    **kwargs :
        Keyword arguments passed to pd.read_csv.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame containing temperature, pressure, and humidity columns.
    """
    if schema is None:
        schema = SensorSchema()

    if data_dir is not None:
        d_path = Path(data_dir)
        if not d_path.exists():
            raise FileNotFoundError(f"Data directory not found: {d_path}")

        # Search for temperature, pressure, humidity files in directory
        if temperature_path is None:
            t_candidates = list(d_path.glob("*temp*.csv"))
            temperature_path = t_candidates[0] if t_candidates else d_path / "temperature.csv"

        if pressure_path is None:
            p_candidates = list(d_path.glob("*press*.csv"))
            pressure_path = p_candidates[0] if p_candidates else d_path / "pressure.csv"

        if humidity_path is None:
            h_candidates = list(d_path.glob("*humid*.csv"))
            humidity_path = h_candidates[0] if h_candidates else d_path / "humidity.csv"

    # Validate file existence
    for label, p in [
        ("Temperature", temperature_path),
        ("Pressure", pressure_path),
        ("Humidity", humidity_path),
    ]:
        if p is None or not Path(p).exists():
            raise FileNotFoundError(f"{label} CSV file not found: {p}")

    df_temp = pd.read_csv(Path(temperature_path), **kwargs)
    df_press = pd.read_csv(Path(pressure_path), **kwargs)
    df_humid = pd.read_csv(Path(humidity_path), **kwargs)

    # Determine join keys (e.g. station_id + timestamp or timestamp alone)
    join_keys: List[str] = []
    if schema.station_id in df_temp.columns and schema.station_id in df_press.columns and schema.station_id in df_humid.columns:
        join_keys.append(schema.station_id)

    if schema.timestamp in df_temp.columns and schema.timestamp in df_press.columns and schema.timestamp in df_humid.columns:
        join_keys.append(schema.timestamp)
    elif schema.original_time in df_temp.columns and schema.original_time in df_press.columns and schema.original_time in df_humid.columns:
        join_keys.append(schema.original_time)

    if not join_keys:
        # Fallback: if no matching timestamp/station column, raise error
        raise ValueError("Could not find common alignment columns (timestamp / station_id) across the 3 files.")

    # Identify metadata columns to preserve from primary dataframe
    meta_cols = [
        col for col in [
            schema.station_id,
            schema.latitude,
            schema.longitude,
            schema.original_time,
            schema.timestamp,
            schema.year,
            schema.month,
            schema.day,
            schema.hour,
            schema.day_of_year,
        ]
        if col in df_temp.columns
    ]

    # Keep only join keys + sensor value for pressure and humidity to prevent duplicate metadata columns
    press_cols = join_keys + [schema.pressure]
    humid_cols = join_keys + [schema.humidity]

    # Filter columns that exist
    press_cols = [c for c in press_cols if c in df_press.columns]
    humid_cols = [c for c in humid_cols if c in df_humid.columns]

    df_merged = pd.merge(df_temp, df_press[press_cols], on=join_keys, how="outer")
    df_merged = pd.merge(df_merged, df_humid[humid_cols], on=join_keys, how="outer")

    # If timestamp column exists, sort by station_id and timestamp
    if schema.timestamp in df_merged.columns:
        sort_cols = [c for c in [schema.station_id, schema.timestamp] if c in df_merged.columns]
        if sort_cols:
            df_merged = df_merged.sort_values(by=sort_cols).reset_index(drop=True)

    return df_merged
