from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema


@dataclass
class SensorStatRecord:
    """Statistical reference metrics for a single sensor variable."""
    count: int = 0
    mean: float = 0.0
    std: float = 0.0
    median: float = 0.0
    q25: float = 0.0
    q75: float = 0.0
    iqr: float = 0.0
    mad: float = 0.0

    @classmethod
    def from_series(cls, series: pd.Series) -> "SensorStatRecord":
        """Compute statistics from a numeric pandas Series."""
        clean = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if len(clean) == 0:
            return cls()

        mean_val = float(clean.mean())
        std_val = float(clean.std(ddof=1)) if len(clean) > 1 else 0.0
        if np.isnan(std_val):
            std_val = 0.0

        median_val = float(clean.median())
        q25 = float(clean.quantile(0.25))
        q75 = float(clean.quantile(0.75))
        iqr_val = max(0.0, q75 - q25)
        mad_val = float((clean - median_val).abs().median())

        return cls(
            count=len(clean),
            mean=mean_val,
            std=std_val,
            median=median_val,
            q25=q25,
            q75=q75,
            iqr=iqr_val,
            mad=mad_val,
        )


@dataclass
class BaselineReference:
    """Container for fitted global, station-specific, and diurnal baseline statistics."""
    global_stats: Dict[str, SensorStatRecord] = field(default_factory=dict)
    station_stats: Dict[str, Dict[str, SensorStatRecord]] = field(default_factory=dict)
    diurnal_stats: Dict[str, Dict[Any, SensorStatRecord]] = field(default_factory=dict)
    station_diurnal_stats: Dict[str, Dict[Tuple[str, int], SensorStatRecord]] = field(default_factory=dict)


def fit_statistical_baselines(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    min_samples_per_bin: int = 5,
) -> BaselineReference:
    """Compute and return reference distributions (global, station, diurnal) from training/reference data.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor dataframe (may contain raw columns and/or engineered features).
    schema : SensorSchema, optional
        Schema definition for column names.
    min_samples_per_bin : int
        Minimum observation count required to establish a valid sub-group baseline.

    Returns
    -------
    BaselineReference
        Fitted baseline reference container.
    """
    if schema is None:
        schema = SensorSchema()

    reference = BaselineReference()
    sensor_cols = [c for c in schema.required_sensor_columns if c in df.columns]

    # 1. Global Baseline Statistics
    for col in sensor_cols:
        reference.global_stats[col] = SensorStatRecord.from_series(df[col])

    # 2. Station-Specific Baseline Statistics
    has_station = schema.station_id in df.columns
    if has_station:
        for col in sensor_cols:
            reference.station_stats[col] = {}
            for stn, group in df.groupby(schema.station_id):
                stn_key = str(stn)
                if len(group) >= min_samples_per_bin:
                    reference.station_stats[col][stn_key] = SensorStatRecord.from_series(group[col])
                else:
                    # Fallback to global if too few samples
                    reference.station_stats[col][stn_key] = reference.global_stats[col]

    # 3. Time-Aware / Diurnal Baselines
    # Extract hour if available
    hour_series = None
    if schema.hour in df.columns:
        hour_series = pd.to_numeric(df[schema.hour], errors="coerce")
    elif schema.timestamp in df.columns:
        hour_series = pd.to_datetime(df[schema.timestamp], errors="coerce").dt.hour

    if hour_series is not None and not hour_series.isna().all():
        df_work = df.copy()
        df_work["_hour_bin"] = hour_series

        for col in sensor_cols:
            reference.diurnal_stats[col] = {}
            # Hourly baseline across all stations
            for h, group in df_work.groupby("_hour_bin"):
                if len(group) >= min_samples_per_bin:
                    reference.diurnal_stats[col][int(h)] = SensorStatRecord.from_series(group[col])
                else:
                    reference.diurnal_stats[col][int(h)] = reference.global_stats[col]

            # Station + Hourly baseline
            if has_station:
                reference.station_diurnal_stats[col] = {}
                for (stn, h), group in df_work.groupby([schema.station_id, "_hour_bin"]):
                    stn_key = str(stn)
                    h_int = int(h)
                    if len(group) >= min_samples_per_bin:
                        reference.station_diurnal_stats[col][(stn_key, h_int)] = SensorStatRecord.from_series(group[col])
                    elif stn_key in reference.station_stats[col]:
                        reference.station_diurnal_stats[col][(stn_key, h_int)] = reference.station_stats[col][stn_key]
                    else:
                        reference.station_diurnal_stats[col][(stn_key, h_int)] = reference.global_stats[col]

    return reference
