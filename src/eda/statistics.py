from pathlib import Path
from typing import Optional, Dict
import pandas as pd
from src.data.schema import SensorSchema


def calculate_sensor_statistics(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Calculate descriptive statistics for temperature, pressure, and humidity.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save sensor_statistics.csv.

    Returns
    -------
    pd.DataFrame
        Summary statistics table for all available sensor columns.
    """
    if schema is None:
        schema = SensorSchema()

    stats_list = []
    for col in schema.required_sensor_columns:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) == 0:
                continue

            q25 = float(s.quantile(0.25))
            q75 = float(s.quantile(0.75))
            iqr = q75 - q25

            stats_list.append({
                "sensor": col,
                "count": int(s.count()),
                "mean": round(float(s.mean()), 4),
                "std": round(float(s.std()), 4),
                "min": round(float(s.min()), 4),
                "25%": round(q25, 4),
                "median": round(float(s.median()), 4),
                "75%": round(q75, 4),
                "max": round(float(s.max()), 4),
                "iqr": round(iqr, 4),
                "skewness": round(float(s.skew()), 4),
                "kurtosis": round(float(s.kurtosis()), 4),
            })

    df_stats = pd.DataFrame(stats_list)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_stats.to_csv(out_p, index=False)

    return df_stats


def calculate_station_statistics(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Calculate sensor statistics broken down by weather station.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save station_statistics.csv.

    Returns
    -------
    pd.DataFrame
        Station-level sensor statistics.
    """
    if schema is None:
        schema = SensorSchema()

    if schema.station_id not in df.columns:
        return pd.DataFrame()

    station_stats = []
    for stn, stn_df in df.groupby(schema.station_id):
        for col in schema.required_sensor_columns:
            if col in stn_df.columns:
                s = pd.to_numeric(stn_df[col], errors="coerce").dropna()
                if len(s) == 0:
                    continue

                q25 = float(s.quantile(0.25))
                q75 = float(s.quantile(0.75))

                station_stats.append({
                    "station_id": stn,
                    "sensor": col,
                    "count": int(s.count()),
                    "mean": round(float(s.mean()), 4),
                    "std": round(float(s.std()), 4),
                    "min": round(float(s.min()), 4),
                    "25%": round(q25, 4),
                    "median": round(float(s.median()), 4),
                    "75%": round(q75, 4),
                    "max": round(float(s.max()), 4),
                    "iqr": round(q75 - q25, 4),
                })

    df_stn_stats = pd.DataFrame(station_stats)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_stn_stats.to_csv(out_p, index=False)

    return df_stn_stats
