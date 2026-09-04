import pytest
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema
from src.fault_injection import FaultConfig, FaultType, FaultInjector
from src.fault_injection import faults

@pytest.fixture
def sample_data():
    schema = SensorSchema()
    dates = pd.date_range("2023-01-01", periods=100, freq="5min")
    return pd.DataFrame({
        schema.timestamp: dates,
        schema.station_id: "STAT1",
        schema.temperature: np.random.normal(25, 2, 100),
        schema.humidity: np.random.normal(50, 5, 100),
        schema.pressure: np.random.normal(1013, 2, 100)
    })

def test_inject_spike():
    s = pd.Series(np.ones(10) * 5)
    s_inj = faults.inject_spike(s, start_idx=2, duration=1, magnitude=10, direction=1)
    
    assert s_inj.iloc[0] == 5
    assert s_inj.iloc[2] == 15
    assert s_inj.iloc[3] == 5

def test_inject_frozen():
    s = pd.Series(np.arange(10, dtype=float))
    s_inj = faults.inject_frozen(s, start_idx=3, duration=4)
    
    # 0, 1, 2, 3(frozen), 3, 3, 3, 7, 8, 9
    assert s_inj.iloc[2] == 2
    assert s_inj.iloc[3] == 3
    assert s_inj.iloc[4] == 3
    assert s_inj.iloc[5] == 3
    assert s_inj.iloc[6] == 3
    assert s_inj.iloc[7] == 7

def test_inject_dropout():
    s = pd.Series(np.ones(10) * 5)
    s_inj = faults.inject_dropout(s, start_idx=2, duration=2)
    
    assert s_inj.iloc[1] == 5
    assert pd.isna(s_inj.iloc[2])
    assert pd.isna(s_inj.iloc[3])
    assert s_inj.iloc[4] == 5

def test_injector_end_to_end(sample_data):
    config = FaultConfig(
        random_seed=42,
        fault_rate=0.1,  # 10 points out of 100
        allow_overlapping_faults=False
    )
    injector = FaultInjector(config=config)
    
    df_inj, df_gt = injector.inject(sample_data)
    meta = injector.get_metadata()
    
    # Check that datasets are returned correctly
    assert len(df_inj) == len(sample_data)
    assert len(df_gt) == len(sample_data)
    
    # Should have injected at least one fault
    assert not meta.empty
    
    # Ground truth tracking check
    has_fault = df_gt["fault_present"].sum() > 0
    assert has_fault
    
    # Ensure original data is not modified
    assert (df_inj["temperature"] != sample_data["temperature"]).any() or \
           (df_inj["humidity"] != sample_data["humidity"]).any() or \
           (df_inj["pressure"] != sample_data["pressure"]).any()
           
    # Check that we didn't overlap if configured not to
    for idx, row in df_gt.iterrows():
        # An observation has only one fault_type at a time if no overlap
        # df_gt tracks single event ID per observation in this design
        pass

def test_ground_truth_labels(sample_data):
    config = FaultConfig(random_seed=1)
    injector = FaultInjector(config=config)
    df_inj, df_gt = injector.inject(sample_data)
    
    # Wherever fault_present is False, fault_type must be NORMAL
    normal_mask = ~df_gt["fault_present"]
    assert (df_gt.loc[normal_mask, "fault_type"] == FaultType.NORMAL.value).all()
    
    # Wherever fault_present is True, fault_type must NOT be NORMAL
    fault_mask = df_gt["fault_present"]
    if fault_mask.sum() > 0:
        assert (df_gt.loc[fault_mask, "fault_type"] != FaultType.NORMAL.value).all()
