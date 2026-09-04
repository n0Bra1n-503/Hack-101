from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from src.data.schema import SensorSchema


def analyze_data_quality(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Analyze dataset quality, missing values, duplicates, and data integrity.

    Parameters
    ----------
    df : pd.DataFrame
        Input sensor DataFrame.
    schema : Optional[SensorSchema]
        Schema specifying sensor and metadata columns.
    output_path : Optional[Path]
        Optional path to save data_quality.csv.

    Returns
    -------
    pd.DataFrame
        Summary of data quality per column.
    """
    if schema is None:
        schema = SensorSchema()

    total_rows = len(df)
    quality_records = []

    # Check whole-row duplicates
    duplicate_rows_count = int(df.duplicated().sum())

    # Check duplicate timestamps per station
    dup_timestamps_count = 0
    if schema.timestamp in df.columns:
        if schema.station_id in df.columns:
            dup_timestamps_count = int(df.duplicated(subset=[schema.station_id, schema.timestamp]).sum())
        else:
            dup_timestamps_count = int(df.duplicated(subset=[schema.timestamp]).sum())

    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = round((null_count / total_rows * 100.0) if total_rows > 0 else 0.0, 3)
        dtype_str = str(df[col].dtype)
        unique_count = int(df[col].nunique(dropna=False))
        is_constant = bool(unique_count <= 1)

        # Check for non-numeric sensor readings if it's a numeric sensor column
        non_numeric_count = 0
        if col in schema.required_sensor_columns:
            non_numeric = pd.to_numeric(df[col], errors="coerce").isnull() & df[col].notnull()
            non_numeric_count = int(non_numeric.sum())

        quality_records.append({
            "column": col,
            "data_type": dtype_str,
            "total_rows": total_rows,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_values": unique_count,
            "is_constant": is_constant,
            "non_numeric_count": non_numeric_count,
            "duplicate_rows_dataset": duplicate_rows_count,
            "duplicate_timestamps": dup_timestamps_count,
        })

    df_quality = pd.DataFrame(quality_records)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_quality.to_csv(out_p, index=False)

    return df_quality
