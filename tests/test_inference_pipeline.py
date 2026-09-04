import pytest
import pandas as pd
from src.pipeline.inference_pipeline import SkyGuardInferencePipeline

@pytest.fixture
def sample_obs():
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "station_id": "STA_1",
        "temperature": 25.0,
        "pressure": 1013.25,
        "humidity": 50.0
    }

def test_pipeline_initialization():
    pipeline = SkyGuardInferencePipeline()
    assert pipeline.if_engine.is_fitted
    assert pipeline.ae_engine.model is not None
    assert pipeline.hybrid_engine is not None
    assert pipeline.decision_engine is not None

def test_inference_single_obs(sample_obs):
    pipeline = SkyGuardInferencePipeline()
    result = pipeline.update(sample_obs)
    
    assert "identification" in result
    assert result["identification"]["station_id"] == "STA_1"
    
    assert "classification" in result
    assert result["classification"] in ["GENUINE_WEATHER", "SENSOR_FAULT", "UNCERTAIN"]
    
    assert "trust_score" in result
    assert 0.0 <= result["trust_score"] <= 100.0
    
    assert "fault_type" in result
    assert result["fault_type"] in ["SPIKE", "DRIFT", "FROZEN", "DROPOUT", "ABRUPT_JUMP", "MULTIVARIATE_INCONSISTENCY", "UNKNOWN", "NONE"]
    
    assert "explanation" in result
    
    # Check that raw input was NOT modified
    assert sample_obs["temperature"] == 25.0

def test_inference_missing_values():
    pipeline = SkyGuardInferencePipeline()
    obs = {
        "timestamp": "2024-01-01T00:00:00Z",
        "station_id": "STA_1",
        "temperature": None,
        "pressure": 1013.25,
        "humidity": 50.0
    }
    result = pipeline.update(obs)
    assert result["classification"] in ["GENUINE_WEATHER", "SENSOR_FAULT", "UNCERTAIN"]
    # Usually dropouts/missing trigger a fault if caught
    # We just ensure it doesn't crash

def test_batch_inference():
    pipeline = SkyGuardInferencePipeline()
    df = pd.DataFrame({
        "timestamp": ["2024-01-01T00:00:00Z", "2024-01-01T00:10:00Z"],
        "station_id": ["STA_1", "STA_1"],
        "temperature": [25.0, 25.2],
        "pressure": [1013.2, 1013.1],
        "humidity": [50.0, 50.5]
    })
    
    res = pipeline.predict_batch(df)
    assert len(res) == 2
    assert "final_classification" in res.columns
    assert "trust_score" in res.columns

def test_inference_invalid_inputs():
    pipeline = SkyGuardInferencePipeline()
    # Missing timestamp
    with pytest.raises(ValueError, match="timestamp"):
        pipeline.update({"station_id": "STA_1", "temperature": 25.0, "pressure": 1013.25, "humidity": 50.0})
    # Malformed timestamp
    with pytest.raises(ValueError, match="timestamp"):
        pipeline.update({"timestamp": "invalid_date", "station_id": "STA_1", "temperature": 25.0, "pressure": 1013.25, "humidity": 50.0})
    # Missing station_id
    with pytest.raises(ValueError, match="station_id"):
        pipeline.update({"timestamp": "2024-01-01T00:00:00Z", "temperature": 25.0, "pressure": 1013.25, "humidity": 50.0})
    # Non-numeric sensor value
    with pytest.raises(ValueError, match="temperature"):
        pipeline.update({"timestamp": "2024-01-01T00:00:00Z", "station_id": "STA_1", "temperature": "hot", "pressure": 1013.25, "humidity": 50.0})

def test_inference_streaming_buffer_window():
    pipeline = SkyGuardInferencePipeline(window_size=10)
    for i in range(25):
        obs = {
            "timestamp": f"2024-01-01T00:{i:02d}:00Z",
            "station_id": "STA_1",
            "temperature": 25.0 + i * 0.05,
            "pressure": 1013.0,
            "humidity": 50.0
        }
        res = pipeline.update(obs)
        assert res["classification"] in ["GENUINE_WEATHER", "SENSOR_FAULT", "UNCERTAIN"]
        assert 0.0 <= res["trust_score"] <= 100.0
        assert not pd.isna(res["anomaly_evidence"]["statistical_anomaly_score"])
    assert len(pipeline._history_buffer) == 10

