import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.schema import SensorSchema
from src.features.pipeline import build_features
from src.features.temporal import build_temporal_features
from src.features.lag_delta import build_lag_delta_features
from src.features.cross_station import build_cross_station_features

@pytest.fixture
def schema():
    return SensorSchema()

@pytest.fixture
def dummy_data(schema):
    """Create a synthetic dataset with multiple stations and timestamps."""
    np.random.seed(42)
    
    stations = ["STN_01", "STN_02", "STN_03"]
    base_time = datetime(2023, 1, 1, 12, 0, 0)
    
    records = []
    
    # 2 hours of data at 5 min intervals (24 points per station)
    for stn in stations:
        for i in range(24):
            dt = base_time + timedelta(minutes=5*i)
            # Create some fake patterns
            temp = 20.0 + np.sin(i * 0.1) * 5 + (np.random.random() - 0.5)
            press = 1013.25 + (np.random.random() - 0.5) * 2
            humid = 50.0 - temp * 0.5 + (np.random.random() - 0.5) * 5
            
            # Intentionally inject some missing data and frozen values
            if i == 5 and stn == "STN_01":
                temp = np.nan
            if i in [10, 11, 12] and stn == "STN_02":
                press = 1000.0  # Frozen value
                
            records.append({
                schema.timestamp: dt,
                schema.station_id: stn,
                schema.temperature: temp,
                schema.pressure: press,
                schema.humidity: humid
            })
            
    df = pd.DataFrame(records)
    return df

def test_temporal_features(dummy_data, schema):
    df_feat, metadata = build_temporal_features(dummy_data, schema)
    
    assert "hour" in df_feat.columns
    assert "day_of_week" in df_feat.columns
    assert "hour_sin" in df_feat.columns
    assert df_feat["hour"].iloc[0] == 12
    assert "hour" in metadata

def test_lag_features_station_isolation(dummy_data, schema):
    """Ensure lag is calculated strictly within a station and does not leak."""
    df_feat, metadata = build_lag_delta_features(dummy_data, schema)
    
    # By default dummy data has 24 points per station. 
    # If grouped correctly, the 1st element of EACH station should have NaN for lag_1
    
    # Get indices for the first row of each station
    first_rows_idx = dummy_data.groupby(schema.station_id).head(1).index
    
    lag_1_col = f"{schema.temperature}_lag_1"
    
    for idx in first_rows_idx:
        assert pd.isna(df_feat.loc[idx, lag_1_col]), f"Data leakage at index {idx}!"

def test_cross_station_exclusion(dummy_data, schema):
    """Ensure a station's own value is excluded from its peer median calculation."""
    df_feat, metadata = build_cross_station_features(dummy_data, schema)
    
    col_median = f"{schema.temperature}_peer_median"
    
    # Let's manually verify one specific timestamp and station
    t0 = dummy_data[schema.timestamp].iloc[0]
    
    # Get all stations at t0
    slice_t0 = dummy_data[dummy_data[schema.timestamp] == t0]
    
    val_stn01 = slice_t0[slice_t0[schema.station_id] == "STN_01"][schema.temperature].values[0]
    val_stn02 = slice_t0[slice_t0[schema.station_id] == "STN_02"][schema.temperature].values[0]
    val_stn03 = slice_t0[slice_t0[schema.station_id] == "STN_03"][schema.temperature].values[0]
    
    idx_stn01 = slice_t0[slice_t0[schema.station_id] == "STN_01"].index[0]
    
    # Peer median for STN_01 should be median(STN_02, STN_03)
    expected_peer_median = np.median([val_stn02, val_stn03])
    
    actual_peer_median = df_feat.loc[idx_stn01, col_median]
    
    assert np.isclose(expected_peer_median, actual_peer_median), "Target station was included in peer median!"

def test_full_pipeline(dummy_data, schema):
    """Test the entire feature pipeline runs and validates successfully."""
    df_final, metadata = build_features(dummy_data, schema)
    
    assert len(df_final) == len(dummy_data)
    assert len(metadata) > 0
    
    # Ensure raw columns still exist
    for col in schema.required_sensor_columns:
        assert col in df_final.columns
        
    # Ensure some engineered columns exist
    assert f"{schema.temperature}_lag_1" in df_final.columns
    assert "hour" in df_final.columns
    assert f"{schema.pressure}_is_missing" in df_final.columns
    assert f"{schema.humidity}_consecutive_identical" in df_final.columns
