import pytest
import pandas as pd
import numpy as np
from src.decision.decision_engine import DecisionEngine
from src.decision.decision_config import DecisionConfig

@pytest.fixture
def sample_data():
    df_hybrid = pd.DataFrame({
        "statistical_anomaly_score": [0.1, 0.2, 0.1, 0.9],
        "isolation_forest_norm": [0.05, 0.1, 0.0, 0.95],
        "autoencoder_norm": [0.02, 0.95, 0.1, 0.8]
    })
    df_stat = pd.DataFrame({
        "is_isolated_sensor_anomaly": [False, True, False, True],
        "is_concurrent_multisensor_anomaly": [False, False, True, False],
        "rolling_deviation_high": [False, True, False, True]
    })
    return df_hybrid, df_stat

def test_genuine_weather(sample_data):
    df_hybrid, df_stat = sample_data
    engine = DecisionEngine(DecisionConfig(weather_threshold=0.4))
    
    # Idx 2 has concurrent multi-sensor, low ML errors. Should be Genuine Weather.
    res = engine.generate_decisions(df_hybrid.iloc[[2]], df_stat.iloc[[2]])
    
    assert res["final_classification"].iloc[0] == "GENUINE_WEATHER"
    assert res["genuine_weather_score"].iloc[0] > 0.4
    assert res["trust_score"].iloc[0] == 100.0 # because of weather bonus

def test_sensor_fault_ae_override(sample_data):
    df_hybrid, df_stat = sample_data
    engine = DecisionEngine(DecisionConfig())
    
    # Idx 1 has low IF, low Stat, but high AE (0.95) and isolated. Should override to SENSOR_FAULT.
    res = engine.generate_decisions(df_hybrid.iloc[[1]], df_stat.iloc[[1]])
    
    assert res["final_classification"].iloc[0] == "SENSOR_FAULT"
    assert res["sensor_fault_score"].iloc[0] >= 0.8
    assert res["fault_type_inferred"].iloc[0] in ["DROPOUT", "FROZEN", "UNKNOWN", "SPIKE"]
    assert res["trust_score"].iloc[0] < 75.0 # penalty for high fault score

def test_normal(sample_data):
    df_hybrid, df_stat = sample_data
    engine = DecisionEngine(DecisionConfig())
    
    # Idx 0 is completely normal.
    res = engine.generate_decisions(df_hybrid.iloc[[0]], df_stat.iloc[[0]])
    
    assert res["final_classification"].iloc[0] == "GENUINE_WEATHER"
    assert res["sensor_fault_score"].iloc[0] < 0.2
    assert res["genuine_weather_score"].iloc[0] < 0.2
    assert res["trust_score"].iloc[0] >= 95.0
