from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema


def analyze_sampling_intervals(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Analyze observation time deltas, median/min/max intervals, and temporal gaps.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save sampling_statistics.csv.

    Returns
    -------
    pd.DataFrame
        Sampling interval statistics per station and overall.
    """
    if schema is None:
        schema = SensorSchema()

    if schema.timestamp not in df.columns:
        return pd.DataFrame()

    df_work = df.copy()
    df_work["_dt"] = pd.to_datetime(df_work[schema.timestamp], errors="coerce")
    df_work = df_work.dropna(subset=["_dt"])

    records = []

    def _calc_intervals(group_df: pd.DataFrame, scope_name: str):
        sorted_ts = group_df["_dt"].sort_values().drop_duplicates()
        if len(sorted_ts) < 2:
            return

        deltas_min = sorted_ts.diff().dt.total_seconds().dropna() / 60.0
        if len(deltas_min) == 0:
            return

        median_int = float(deltas_min.median())
        mode_val = float(deltas_min.mode().iloc[0]) if not deltas_min.mode().empty else median_int
        min_int = float(deltas_min.min())
        max_int = float(deltas_min.max())
        mean_int = float(deltas_min.mean())
        # Large gaps defined as intervals > 2x median interval
        large_gaps_count = int((deltas_min > (median_int * 2.0)).sum())

        records.append({
            "scope": scope_name,
            "total_timestamps": len(sorted_ts),
            "median_interval_minutes": round(median_int, 2),
            "common_interval_minutes": round(mode_val, 2),
            "min_interval_minutes": round(min_int, 2),
            "max_interval_minutes": round(max_int, 2),
            "mean_interval_minutes": round(mean_int, 2),
            "large_gaps_count": large_gaps_count,
            "start_time": str(sorted_ts.min()),
            "end_time": str(sorted_ts.max()),
        })

    # Overall
    _calc_intervals(df_work, "OVERALL")

    # Per Station
    if schema.station_id in df_work.columns:
        for stn, stn_df in df_work.groupby(schema.station_id):
            _calc_intervals(stn_df, f"Station: {stn}")

    df_sampling = pd.DataFrame(records)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_sampling.to_csv(out_p, index=False)

    return df_sampling


def analyze_temporal_patterns(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Analyze diurnal (hourly) patterns across sensors.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save temporal_patterns.csv.

    Returns
    -------
    pd.DataFrame
        Diurnal statistics (mean, std, min, max) for each hour (0-23).
    """
    if schema is None:
        schema = SensorSchema()

    df_work = df.copy()
    if "hour" in df_work.columns:
        hours = pd.to_numeric(df_work["hour"], errors="coerce")
    elif schema.timestamp in df_work.columns:
        dt = pd.to_datetime(df_work[schema.timestamp], errors="coerce")
        hours = dt.dt.hour
    else:
        return pd.DataFrame()

    df_work["_hour"] = hours
    df_work = df_work.dropna(subset=["_hour"])
    df_work["_hour"] = df_work["_hour"].astype(int)

    pattern_rows = []
    for h, h_df in df_work.groupby("_hour"):
        row: Dict[str, Any] = {"hour": int(h)}
        for s in schema.required_sensor_columns:
            if s in h_df.columns:
                vals = pd.to_numeric(h_df[s], errors="coerce").dropna()
                if len(vals) > 0:
                    row[f"{s}_mean"] = round(float(vals.mean()), 3)
                    row[f"{s}_std"] = round(float(vals.std()), 3)
                    row[f"{s}_min"] = round(float(vals.min()), 3)
                    row[f"{s}_max"] = round(float(vals.max()), 3)
        pattern_rows.append(row)

    df_patterns = pd.DataFrame(pattern_rows).sort_values("hour").reset_index(drop=True)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_patterns.to_csv(out_p, index=False)

    return df_patterns
