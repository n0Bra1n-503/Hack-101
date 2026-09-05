import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.data.schema import SensorSchema

def build_cross_station_features(df: pd.DataFrame, schema: SensorSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate cross-station consistency features, strictly excluding the target station from its baseline."""
    df_feat = pd.DataFrame(index=df.index)
    metadata = {}
    
    if schema.station_id not in df.columns or schema.timestamp not in df.columns:
        return df_feat, metadata
        
    for sensor in schema.required_sensor_columns:
        if sensor not in df.columns:
            continue
            
        # We need to compute the median/mean of peers EXCLUDING the current station
        # A vectorized way to do this is to compute the sum and count for all stations at that timestamp,
        # then for each station, subtract its value from the sum and divide by count - 1 (for mean).
        # For median, it's safer to pivot, and for each station, compute median of other columns.
        
        pivot = df.pivot_table(index=schema.timestamp, columns=schema.station_id, values=sensor, aggfunc="mean")
        if pivot.shape[1] < 2:
            continue
            
        col_dev = f"{sensor}_dev_peer_median"
        col_peer_median = f"{sensor}_peer_median"
        
        df_feat[col_peer_median] = np.nan
        df_feat[col_dev] = np.nan
        
        # Merge back the results using timestamp and station_id as index
        # We'll calculate the peer median for each station column
        result_records = []
        for stn in pivot.columns:
            # All other stations
            peer_cols = [c for c in pivot.columns if c != stn]
            # Median of peers
            peer_median = pivot[peer_cols].median(axis=1)
            
            # Create a dataframe for this station to merge back
            stn_df = pd.DataFrame({
                schema.timestamp: peer_median.index,
                schema.station_id: stn,
                col_peer_median: peer_median.values
            })
            result_records.append(stn_df)
            
        if result_records:
            peer_df = pd.concat(result_records, ignore_index=True)
            
            # Merge peer_df onto the original df based on timestamp and station_id
            # To ensure exact index alignment, we merge and then assign
            temp_df = df[[schema.station_id, schema.timestamp]].copy()
            temp_df["__original_index"] = temp_df.index
            
            merged = pd.merge(temp_df, peer_df, on=[schema.station_id, schema.timestamp], how="left")
            merged = merged.sort_values("__original_index").set_index("__original_index")
            
            df_feat[col_peer_median] = merged[col_peer_median]
            
            # Deviation from peer median
            s_series = pd.to_numeric(df[sensor], errors="coerce")
            df_feat[col_dev] = s_series - df_feat[col_peer_median]
            
            metadata[col_peer_median] = {
                "category": "cross_station", 
                "description": f"Median of {sensor} across all other stations at the same timestamp", 
                "uses_history": False, 
                "can_contain_nan": True
            }
            metadata[col_dev] = {
                "category": "cross_station", 
                "description": f"Deviation of {sensor} from peer station median", 
                "uses_history": False, 
                "can_contain_nan": True
            }

    return df_feat, metadata
