import pandas as pd
from typing import Dict, Any, Tuple
from src.data.schema import SensorSchema

def build_rolling_features(df: pd.DataFrame, schema: SensorSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate rolling window statistics and baseline deviation features."""
    df_feat = pd.DataFrame(index=df.index)
    metadata = {}
    
    has_station = schema.station_id in df.columns
    
    # 5 min sampling -> 6 steps = 30 mins, 24 steps = 2 hours
    windows = [6, 24]
    
    for sensor in schema.required_sensor_columns:
        if sensor not in df.columns:
            continue
            
        s_series = pd.to_numeric(df[sensor], errors="coerce")
        
        for w in windows:
            # We must use closed='left' (or shift) to prevent data leakage from the current time step t!
            # We want rolling stats for [t-w, t-1]
            if has_station:
                roll_obj = df.groupby(schema.station_id)[sensor].shift(1).groupby(df[schema.station_id]).rolling(window=w, min_periods=max(1, w//2))
            else:
                roll_obj = s_series.shift(1).rolling(window=w, min_periods=max(1, w//2))
                
            col_mean = f"{sensor}_roll_mean_{w}"
            col_std = f"{sensor}_roll_std_{w}"
            col_min = f"{sensor}_roll_min_{w}"
            col_max = f"{sensor}_roll_max_{w}"
            
            # Note: the double groupby in pandas for rolling can be tricky with indices. 
            # Safer approach for shifted rolling:
            if has_station:
                grouped = df.groupby(schema.station_id)[sensor]
                shifted = grouped.shift(1)
                
                # We need to re-group the shifted series by station to apply rolling safely
                # creating a temporary dataframe with station_id and the shifted values
                temp_df = pd.DataFrame({"stn": df[schema.station_id], "val": shifted})
                roll = temp_df.groupby("stn")["val"].rolling(window=w, min_periods=max(1, w//2))
                
                # The index of roll output is a MultiIndex (stn, original_index). We need to drop stn and re-align
                df_feat[col_mean] = roll.mean().reset_index(level=0, drop=True).sort_index()
                df_feat[col_std] = roll.std().reset_index(level=0, drop=True).sort_index()
                df_feat[col_min] = roll.min().reset_index(level=0, drop=True).sort_index()
                df_feat[col_max] = roll.max().reset_index(level=0, drop=True).sort_index()
            else:
                shifted = s_series.shift(1)
                roll = shifted.rolling(window=w, min_periods=max(1, w//2))
                df_feat[col_mean] = roll.mean()
                df_feat[col_std] = roll.std()
                df_feat[col_min] = roll.min()
                df_feat[col_max] = roll.max()
                
            metadata[col_mean] = {"category": "rolling", "description": f"Rolling mean of {sensor} over {w} steps prior", "uses_history": True, "can_contain_nan": True}
            metadata[col_std] = {"category": "rolling", "description": f"Rolling std of {sensor} over {w} steps prior", "uses_history": True, "can_contain_nan": True}
            metadata[col_min] = {"category": "rolling", "description": f"Rolling min of {sensor} over {w} steps prior", "uses_history": True, "can_contain_nan": True}
            metadata[col_max] = {"category": "rolling", "description": f"Rolling max of {sensor} over {w} steps prior", "uses_history": True, "can_contain_nan": True}

            # Baseline deviation: how far is current value from the rolling mean baseline
            col_dev_abs = f"{sensor}_dev_roll_mean_{w}"
            df_feat[col_dev_abs] = s_series - df_feat[col_mean]
            metadata[col_dev_abs] = {"category": "baseline_deviation", "description": f"Absolute deviation from {w}-step rolling mean", "uses_history": True, "can_contain_nan": True}
            
            # Z-score baseline deviation: (val - mean) / std
            # Protect against division by zero (std = 0)
            col_dev_z = f"{sensor}_zscore_roll_{w}"
            safe_std = df_feat[col_std].replace(0, 1e-5)
            df_feat[col_dev_z] = df_feat[col_dev_abs] / safe_std
            metadata[col_dev_z] = {"category": "baseline_deviation", "description": f"Z-score deviation from {w}-step rolling distribution", "uses_history": True, "can_contain_nan": True}
            
    return df_feat, metadata
