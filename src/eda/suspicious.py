from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema


def identify_potentially_suspicious(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Perform exploratory statistical checks to flag candidate observations for investigation.

    Checks:
    - Physical climatological range boundaries.
    - Extreme rate of change across consecutive observations.
    - Stuck / flatline identical readings across consecutive samples.
    - Large cross-station disagreement (> 4 standard deviations from cross-station median).

    Note: These are preliminary exploratory flags and do NOT constitute confirmed sensor faults.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save potentially_suspicious.csv.

    Returns
    -------
    pd.DataFrame
        Table of potentially suspicious observations.
    """
    if schema is None:
        schema = SensorSchema()

    df_work = df.copy()
    if schema.timestamp in df_work.columns:
        df_work["_dt"] = pd.to_datetime(df_work[schema.timestamp], errors="coerce")
        df_work = df_work.sort_values(by=[c for c in [schema.station_id, "_dt"] if c in df_work.columns]).reset_index(drop=True)

    flagged_records: List[Dict[str, Any]] = []

    # 1. Physical Climatological Limits
    limits = {
        schema.temperature: (-20.0, 60.0),
        schema.pressure: (800.0, 1100.0),
        schema.humidity: (0.0, 100.0),
    }

    for sensor, (lower, upper) in limits.items():
        if sensor in df_work.columns:
            vals = pd.to_numeric(df_work[sensor], errors="coerce")
            out_of_bounds = df_work[(vals < lower) | (vals > upper)]
            for _, row in out_of_bounds.iterrows():
                flagged_records.append({
                    "station_id": row.get(schema.station_id, "Unknown"),
                    "timestamp": row.get(schema.timestamp, "Unknown"),
                    "sensor": sensor,
                    "value": row[sensor],
                    "reason": f"Physical range exceeded ({lower} to {upper})",
                    "metric_value": float(row[sensor]),
                })

    # Group by station for time-series rate of change and stuck sensor checks
    station_groups = df_work.groupby(schema.station_id) if schema.station_id in df_work.columns else [( "All", df_work )]

    rate_limits = {
        schema.temperature: 4.0,   # > 4°C jump in single interval
        schema.pressure: 3.0,      # > 3 hPa jump in single interval
        schema.humidity: 25.0,     # > 25% jump in single interval
    }

    for stn_id, g in station_groups:
        for sensor, delta_thresh in rate_limits.items():
            if sensor in g.columns:
                s = pd.to_numeric(g[sensor], errors="coerce")
                diffs = s.diff().abs()
                spike_rows = g[diffs > delta_thresh]
                for idx, row in spike_rows.iterrows():
                    d_val = float(diffs.loc[idx])
                    flagged_records.append({
                        "station_id": stn_id,
                        "timestamp": row.get(schema.timestamp, "Unknown"),
                        "sensor": sensor,
                        "value": row[sensor],
                        "reason": f"High rate of change (|Δ| = {d_val:.2f} > {delta_thresh})",
                        "metric_value": d_val,
                    })

                # Check for stuck / flatline identical readings (>= 8 consecutive identical values)
                diff_zeros = (diffs == 0.0).astype(int)
                # Group consecutive zeros
                blocks = (diff_zeros != diff_zeros.shift()).cumsum()
                run_lengths = diff_zeros.groupby(blocks).transform("sum")
                flatline_rows = g[(diff_zeros == 1) & (run_lengths >= 8)]
                for idx, row in flatline_rows.iterrows():
                    flagged_records.append({
                        "station_id": stn_id,
                        "timestamp": row.get(schema.timestamp, "Unknown"),
                        "sensor": sensor,
                        "value": row[sensor],
                        "reason": f"Prolonged invariant reading (flatline run >= 8)",
                        "metric_value": float(row[sensor]),
                    })

    # Cross-station disagreement check (> 4 sigma from cross-station median)
    if schema.station_id in df_work.columns and schema.timestamp in df_work.columns:
        for sensor in schema.required_sensor_columns:
            if sensor not in df_work.columns:
                continue

            pivot = df_work.pivot_table(
                index=schema.timestamp,
                columns=schema.station_id,
                values=sensor,
                aggfunc="mean",
            )
            if pivot.shape[1] >= 3:
                medians = pivot.median(axis=1)
                stds = pivot.std(axis=1).replace(0, np.nan)

                for stn in pivot.columns:
                    devs = (pivot[stn] - medians).abs()
                    z_scores = (devs / stds).dropna()
                    extreme_devs = z_scores[z_scores > 4.0]
                    for ts, z_val in extreme_devs.items():
                        raw_val = pivot.loc[ts, stn]
                        flagged_records.append({
                            "station_id": stn,
                            "timestamp": str(ts),
                            "sensor": sensor,
                            "value": raw_val,
                            "reason": f"Unusual cross-station disagreement (z-score = {z_val:.2f} > 4.0)",
                            "metric_value": round(float(z_val), 2),
                        })

    df_suspicious = pd.DataFrame(flagged_records)
    if not df_suspicious.empty:
        # Drop exact duplicate flagged records if any
        df_suspicious = df_suspicious.drop_duplicates(subset=["station_id", "timestamp", "sensor", "reason"]).reset_index(drop=True)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_suspicious.to_csv(out_p, index=False)

    return df_suspicious
