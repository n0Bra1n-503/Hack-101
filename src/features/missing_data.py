import pandas as pd
from typing import Dict, Any, Tuple
from src.data.schema import SensorSchema

def build_missing_data_features(df: pd.DataFrame, schema: SensorSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate features tracking missing values and gaps (sensor dropout)."""
    df_feat = pd.DataFrame(index=df.index)
    metadata = {}
    
    # Simple flags for missingness
    for sensor in schema.required_sensor_columns:
        if sensor in df.columns:
            col_missing = f"{sensor}_is_missing"
            df_feat[col_missing] = df[sensor].isnull().astype(int)
            metadata[col_missing] = {
                "category": "missing_data",
                "description": f"Binary flag indicating if {sensor} reading is missing",
                "uses_history": False,
                "can_contain_nan": False
            }
            
    # Gap duration (time since previous valid observation for the whole station)
    if schema.timestamp in df.columns:
        col_gap = "time_since_previous_obs_mins"
        df_work = pd.DataFrame(index=df.index)
        df_work["_dt"] = pd.to_datetime(df[schema.timestamp], errors="coerce")
        
        if schema.station_id in df.columns:
            df_feat[col_gap] = df_work.groupby(df[schema.station_id])["_dt"].diff().dt.total_seconds() / 60.0
        else:
            df_feat[col_gap] = df_work["_dt"].diff().dt.total_seconds() / 60.0
            
        metadata[col_gap] = {
            "category": "missing_data",
            "description": "Minutes since previous observation for the station",
            "uses_history": True,
            "can_contain_nan": True
        }

    return df_feat, metadata
