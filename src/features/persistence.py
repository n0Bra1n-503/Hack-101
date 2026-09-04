import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.data.schema import SensorSchema

def build_persistence_features(df: pd.DataFrame, schema: SensorSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate features tracking consecutive identical readings (frozen sensor) or duration since change."""
    df_feat = pd.DataFrame(index=df.index)
    metadata = {}
    
    has_station = schema.station_id in df.columns
    
    for sensor in schema.required_sensor_columns:
        if sensor not in df.columns:
            continue
            
        s_series = pd.to_numeric(df[sensor], errors="coerce")
        col_frozen = f"{sensor}_consecutive_identical"
        
        if has_station:
            # We want to count how many consecutive times the value has remained exactly the same up to time t
            # diff() == 0 means it's the same as previous.
            # cumsum() of (diff != 0) gives a unique ID to each block of identical values.
            # Then we groupby(station, block_id) and use cumcount() to get the running count of identical values.
            
            diff_not_zero = (df.groupby(schema.station_id)[sensor].diff() != 0).astype(int)
            blocks = diff_not_zero.groupby(df[schema.station_id]).cumsum()
            
            # Now we group by station and the block ID, and count incrementally
            # cumcount() starts at 0 for the first item in the block.
            df_feat[col_frozen] = df.groupby([schema.station_id, blocks]).cumcount()
            
        else:
            diff_not_zero = (s_series.diff() != 0).astype(int)
            blocks = diff_not_zero.cumsum()
            df_feat[col_frozen] = s_series.groupby(blocks).cumcount()
            
        metadata[col_frozen] = {
            "category": "persistence", 
            "description": f"Number of consecutive identical readings for {sensor} up to current step", 
            "uses_history": True, 
            "can_contain_nan": False
        }

    return df_feat, metadata
