import pytest
import pandas as pd
import numpy as np
from src.evidence.hybrid_engine import HybridEvidenceEngine
from src.evidence.hybrid_config import HybridEngineConfig

@pytest.fixture
def sample_data():
    df_raw = pd.DataFrame({"dummy": [1, 2, 3]})
    df_stat = pd.DataFrame({
        "statistical_anomaly_score": [0.1, 0.8, 0.2],
        "rolling_deviation_high": [False, True, False],
        "is_concurrent_multisensor_anomaly": [False, True, False]
    })
    df_if = pd.DataFrame({"anomaly_score": [0.05, 0.95, 0.1]})
    df_ae = pd.DataFrame({"anomaly_score": [0.02, 1.5, 0.03]})
    return df_raw, df_stat, df_if, df_ae

def test_hybrid_engine_normalization(sample_data):
    df_raw, df_stat, df_if, df_ae = sample_data
    
    config = HybridEngineConfig(norm_percentile=100.0)
    engine = HybridEvidenceEngine(config)
    
    # Fit on same data just for test
    engine.fit_normalizers(df_if, df_ae)
    
    # IF norm: max is 0.95, min is 0.05 -> idx 1 becomes 1.0, idx 0 becomes 0.0
    res = engine.generate_hybrid_evidence(df_raw, df_stat, df_if, df_ae)
    
    assert np.isclose(res["isolation_forest_norm"].iloc[1], 1.0)
    assert np.isclose(res["isolation_forest_norm"].iloc[0], 0.0)
    
    assert np.isclose(res["autoencoder_norm"].iloc[1], 1.0)
    assert np.isclose(res["autoencoder_norm"].iloc[0], 0.0)

def test_hybrid_score_calculation(sample_data):
    df_raw, df_stat, df_if, df_ae = sample_data
    
    config = HybridEngineConfig(
        w_statistical=0.25,
        w_isolation_forest=0.25,
        w_autoencoder=0.25,
        w_temporal_persistence=0.125,
        w_cross_sensor=0.125,
        norm_percentile=100.0
    )
    engine = HybridEvidenceEngine(config)
    engine.fit_normalizers(df_if, df_ae)
    
    res = engine.generate_hybrid_evidence(df_raw, df_stat, df_if, df_ae)
    
    # Idx 1:
    # Stat = 0.8
    # IF_norm = 1.0
    # AE_norm = 1.0
    # temporal = 1.0
    # cross = 1.0
    # Weighted sum: (0.8*0.25) + (1.0*0.25) + (1.0*0.25) + (1.0*0.125) + (1.0*0.125) 
    # = 0.2 + 0.25 + 0.25 + 0.125 + 0.125 = 0.95
    assert np.isclose(res["hybrid_score"].iloc[1], 0.95)
    assert res["evidence_strength"].iloc[1] == "HIGH"
    assert "reasons" in res.columns or "evidence_reasons" in res.columns
    
def test_missing_evidence_sources(sample_data):
    df_raw, df_stat, _, _ = sample_data
    # Empty DFs for ML
    df_if = pd.DataFrame(index=df_raw.index)
    df_ae = pd.DataFrame(index=df_raw.index)
    
    engine = HybridEvidenceEngine()
    engine.fit_normalizers(df_if, df_ae)
    
    res = engine.generate_hybrid_evidence(df_raw, df_stat, df_if, df_ae)
    
    assert (res["isolation_forest_norm"] == 0).all()
    assert (res["autoencoder_norm"] == 0).all()
    # It shouldn't crash
    assert len(res) == len(df_raw)
