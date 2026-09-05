from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema


def analyze_stations(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Analyze station coverage, total records, time bounds, and coordinates.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save station_coverage.csv.

    Returns
    -------
    pd.DataFrame
        Summary table per station.
    """
    if schema is None:
        schema = SensorSchema()

    if schema.station_id not in df.columns:
        return pd.DataFrame()

    records = []
    for stn, stn_df in df.groupby(schema.station_id):
        rec: Dict[str, Any] = {
            "station_id": stn,
            "record_count": len(stn_df),
        }

        if schema.latitude in stn_df.columns:
            rec["latitude"] = float(stn_df[schema.latitude].iloc[0])
        if schema.longitude in stn_df.columns:
            rec["longitude"] = float(stn_df[schema.longitude].iloc[0])

        if schema.timestamp in stn_df.columns:
            rec["start_timestamp"] = str(stn_df[schema.timestamp].min())
            rec["end_timestamp"] = str(stn_df[schema.timestamp].max())

        for s in schema.required_sensor_columns:
            if s in stn_df.columns:
                rec[f"{s}_missing_count"] = int(stn_df[s].isnull().sum())
                rec[f"{s}_missing_pct"] = round(float(stn_df[s].isnull().mean() * 100.0), 2)

        records.append(rec)

    df_stations = pd.DataFrame(records)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_stations.to_csv(out_p, index=False)

    return df_stations


def analyze_cross_station(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Analyze cross-station consistency and station deviations from group median.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save cross_station_summary.csv.

    Returns
    -------
    pd.DataFrame
        Cross-station comparison summary per station and sensor.
    """
    if schema is None:
        schema = SensorSchema()

    if schema.station_id not in df.columns or schema.timestamp not in df.columns:
        return pd.DataFrame()

    # Create pivot table per sensor indexed by timestamp with stations as columns
    summary_rows = []

    for s in schema.required_sensor_columns:
        if s not in df.columns:
            continue

        pivot = df.pivot_table(
            index=schema.timestamp,
            columns=schema.station_id,
            values=s,
            aggfunc="mean",
        )

        if pivot.shape[1] < 2:
            continue  # Single station, cross-station not applicable

        group_median = pivot.median(axis=1)
        group_mean = pivot.mean(axis=1)
        group_std = pivot.std(axis=1)

        for stn_col in pivot.columns:
            stn_series = pivot[stn_col]
            dev_from_median = (stn_series - group_median).dropna()
            dev_from_mean = (stn_series - group_mean).dropna()

            if len(dev_from_median) == 0:
                continue

            summary_rows.append({
                "station_id": stn_col,
                "sensor": s,
                "common_timestamps_count": int(dev_from_median.count()),
                "mean_deviation": round(float(dev_from_median.mean()), 4),
                "median_deviation": round(float(dev_from_median.median()), 4),
                "mean_absolute_deviation": round(float(dev_from_median.abs().mean()), 4),
                "max_positive_deviation": round(float(dev_from_median.max()), 4),
                "max_negative_deviation": round(float(dev_from_median.min()), 4),
                "std_deviation": round(float(dev_from_median.std()), 4),
            })

    df_cross = pd.DataFrame(summary_rows)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_cross.to_csv(out_p, index=False)

    return df_cross
