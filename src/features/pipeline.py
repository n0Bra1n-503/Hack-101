import pandas as pd
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import numpy as np
from src.data.schema import SensorSchema

from .temporal import build_temporal_features
from .lag_delta import build_lag_delta_features
from .rolling import build_rolling_features
from .cross_sensor import build_cross_sensor_features
from .cross_station import build_cross_station_features
from .persistence import build_persistence_features
from .missing_data import build_missing_data_features

def validate_features(df_raw: pd.DataFrame, df_feat: pd.DataFrame, schema: SensorSchema) -> None:
    """Validate the generated feature dataframe for row count, inf values, and structural integrity."""
    if len(df_raw) != len(df_feat):
        raise ValueError(f"Row count mismatch: Raw ({len(df_raw)}) vs Features ({len(df_feat)})")
        
    # Check for infinite values
    inf_cols = []
    for col in df_feat.columns:
        if pd.api.types.is_numeric_dtype(df_feat[col]):
            if np.isinf(df_feat[col]).any():
                inf_cols.append(col)
                
    if inf_cols:
        raise ValueError(f"Infinite values detected in engineered features: {inf_cols}")
        
    # Ensure raw data was not modified (basic check)
    # We do this by checking if the output DataFrame has completely different columns than raw (except for joins)
    # Actually, we will concatenate them later, so df_feat should initially contain ONLY new columns.
    common_cols = set(df_raw.columns).intersection(set(df_feat.columns))
    if common_cols:
        raise ValueError(f"Feature engineering overwritten existing raw columns: {common_cols}")

def build_features(
    df: pd.DataFrame, 
    schema: Optional[SensorSchema] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main feature engineering pipeline.
    Preserves raw data and appends engineered features.
    
    Returns:
        pd.DataFrame: Combined DataFrame (raw + engineered features).
        Dict: Metadata for all engineered features.
    """
    if schema is None:
        schema = SensorSchema()
        
    # Sort data chronologically to ensure safe historical calculations
    df_sorted = df.copy()
    if schema.timestamp in df_sorted.columns:
        df_sorted["_dt"] = pd.to_datetime(df_sorted[schema.timestamp], errors="coerce")
        sort_keys = [c for c in [schema.station_id, "_dt"] if c in df_sorted.columns]
        df_sorted = df_sorted.sort_values(by=sort_keys).reset_index(drop=True)
        df_sorted = df_sorted.drop(columns=["_dt"])

    # Keep track of all feature dataframes to concatenate later
    feature_dfs = []
    full_metadata = {}
    
    # 1. Temporal
    df_temp, meta_temp = build_temporal_features(df_sorted, schema)
    feature_dfs.append(df_temp)
    full_metadata.update(meta_temp)
    
    # 2. Lag and Delta
    df_lag, meta_lag = build_lag_delta_features(df_sorted, schema)
    feature_dfs.append(df_lag)
    full_metadata.update(meta_lag)
    
    # 3. Rolling Statistics and Baseline Deviation
    df_roll, meta_roll = build_rolling_features(df_sorted, schema)
    feature_dfs.append(df_roll)
    full_metadata.update(meta_roll)
    
    # 4. Cross-Sensor Relationships
    df_cs, meta_cs = build_cross_sensor_features(df_sorted, schema)
    feature_dfs.append(df_cs)
    full_metadata.update(meta_cs)
    
    # 5. Cross-Station Consistency (Excluding target station)
    df_cstn, meta_cstn = build_cross_station_features(df_sorted, schema)
    feature_dfs.append(df_cstn)
    full_metadata.update(meta_cstn)
    
    # 6. Persistence (Frozen sensors)
    df_pers, meta_pers = build_persistence_features(df_sorted, schema)
    feature_dfs.append(df_pers)
    full_metadata.update(meta_pers)
    
    # 7. Missing Data
    df_miss, meta_miss = build_missing_data_features(df_sorted, schema)
    feature_dfs.append(df_miss)
    full_metadata.update(meta_miss)
    
    # Combine all feature dataframes
    df_engineered = pd.concat(feature_dfs, axis=1)
    
    # Validate
    validate_features(df_sorted, df_engineered, schema)
    
    # Final output combines raw (sorted) + engineered
    df_final = pd.concat([df_sorted, df_engineered], axis=1)
    
    return df_final, full_metadata

def save_feature_metadata(metadata: Dict[str, Any], output_path: Path):
    """Save feature metadata as JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
def generate_feature_summary(df_feat: pd.DataFrame, metadata: Dict[str, Any], output_path: Path):
    """Generate a CSV summary of the engineered features."""
    summary_rows = []
    
    for feat_name, meta in metadata.items():
        if feat_name in df_feat.columns:
            s = df_feat[feat_name]
            null_pct = round(s.isnull().mean() * 100.0, 2)
            unique_vals = s.nunique(dropna=False)
            dtype = str(s.dtype)
            
            summary_rows.append({
                "feature_name": feat_name,
                "category": meta.get("category", "unknown"),
                "dtype": dtype,
                "missing_pct": null_pct,
                "unique_values": unique_vals,
                "description": meta.get("description", "")
            })
            
    df_summary = pd.DataFrame(summary_rows)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(output_path, index=False)
