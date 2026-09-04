import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.data.schema import SensorSchema

def build_temporal_features(df: pd.DataFrame, schema: SensorSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate temporal features (hour, day of week, cyclical encodings)."""
    df_feat = pd.DataFrame(index=df.index)
    metadata = {}
    
    if schema.timestamp not in df.columns:
        return df_feat, metadata
        
    dt_series = pd.to_datetime(df[schema.timestamp], errors="coerce")
    
    # Base temporal features
    hour_series = dt_series.dt.hour if schema.timestamp in df.columns else (df[schema.hour] if schema.hour in df.columns else None)
    
    if "hour" not in df.columns and hour_series is not None:
        df_feat["hour"] = hour_series
        metadata["hour"] = {"category": "temporal", "description": "Hour of the day (0-23)", "uses_history": False}
        
    if "day_of_week" not in df.columns and dt_series is not None:
        df_feat["day_of_week"] = dt_series.dt.dayofweek
        metadata["day_of_week"] = {"category": "temporal", "description": "Day of the week (0-6)", "uses_history": False}
        
    if "day_of_year" not in df.columns and dt_series is not None:
        df_feat["day_of_year"] = dt_series.dt.dayofyear
        metadata["day_of_year"] = {"category": "temporal", "description": "Day of the year (1-366)", "uses_history": False}

    # Cyclical encoding for hour (24-hour cycle)
    if hour_series is not None:
        df_feat["hour_sin"] = np.sin(2 * np.pi * hour_series / 24.0)
        df_feat["hour_cos"] = np.cos(2 * np.pi * hour_series / 24.0)
        metadata["hour_sin"] = {"category": "temporal", "description": "Sine encoding of hour", "uses_history": False}
        metadata["hour_cos"] = {"category": "temporal", "description": "Cosine encoding of hour", "uses_history": False}

    return df_feat, metadata
