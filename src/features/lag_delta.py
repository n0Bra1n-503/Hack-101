import pandas as pd
from typing import Dict, Any, Tuple
from src.data.schema import SensorSchema

def build_lag_delta_features(df: pd.DataFrame, schema: SensorSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate lag and delta (change) features for sensor readings."""
    df_feat = pd.DataFrame(index=df.index)
    metadata = {}
    
    # We need station grouping to avoid leaking data across stations
    has_station = schema.station_id in df.columns
    
    # Define lags based on ~5 min sampling: 1 step (5m), 3 steps (15m)
    lags = [1, 3]
    
    for sensor in schema.required_sensor_columns:
        if sensor not in df.columns:
            continue
            
        s_series = pd.to_numeric(df[sensor], errors="coerce")
        
        for lag in lags:
            col_name_lag = f"{sensor}_lag_{lag}"
            col_name_delta = f"{sensor}_delta_{lag}"
            
            if has_station:
                # Group by station to calculate lag safely without cross-station leakage
                df_feat[col_name_lag] = df.groupby(schema.station_id)[sensor].shift(lag)
            else:
                df_feat[col_name_lag] = s_series.shift(lag)
                
            # Delta feature (Current - Lag)
            df_feat[col_name_delta] = s_series - df_feat[col_name_lag]
            
            metadata[col_name_lag] = {
                "category": "lag",
                "description": f"Value of {sensor} {lag} steps ago",
                "source_sensor": sensor,
                "uses_history": True,
                "can_contain_nan": True
            }
            metadata[col_name_delta] = {
                "category": "delta",
                "description": f"Difference in {sensor} compared to {lag} steps ago",
                "source_sensor": sensor,
                "uses_history": True,
                "can_contain_nan": True
            }
            
    return df_feat, metadata
