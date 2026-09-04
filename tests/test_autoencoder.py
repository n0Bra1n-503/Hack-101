import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.data.schema import SensorSchema
from src.models.autoencoder import AutoencoderEngine, get_autoencoder_features
from src.models.autoencoder_config import AutoencoderConfig

@pytest.fixture
def sample_data():
    schema = SensorSchema()
    dates = pd.date_range("2023-01-01", periods=100, freq="5min")
    return pd.DataFrame({
        schema.timestamp: dates,
        schema.station_id: "STAT1",
        schema.temperature: np.random.normal(25, 2, 100),
        schema.humidity: np.random.normal(50, 5, 100),
        schema.pressure: np.random.normal(1013, 2, 100),
        "fault_present": False,
        "fault_type": "NORMAL"
    })

def test_feature_selection(sample_data):
    features = get_autoencoder_features(sample_data)
    
    assert "fault_present" not in features
    assert "fault_type" not in features
    assert "station_id" not in features
    assert "timestamp" not in features
    assert "temperature" in features
    assert "pressure" in features
    assert "humidity" in features

def test_engine_fit_predict(sample_data):
    config = AutoencoderConfig(epochs=2, batch_size=32, hidden_dims=(16, 8, 16))
    engine = AutoencoderEngine(config=config)
    
    history = engine.fit(sample_data)
    assert engine.is_fitted
    assert len(history["train_loss"]) > 0
    
    # Predict
    results = engine.predict(sample_data)
    assert "anomaly_score" in results.columns
    assert "anomaly_prediction" in results.columns
    
    # Assert manual boolean logic matches predictions based on threshold
    manual_preds = results["anomaly_score"] >= engine.threshold
    pd.testing.assert_series_equal(results["anomaly_prediction"], manual_preds, check_names=False)

def test_missing_data_imputation(sample_data):
    df_nan = sample_data.copy()
    df_nan.loc[0, "temperature"] = np.nan
    df_nan.loc[1, "pressure"] = np.nan
    
    config = AutoencoderConfig(epochs=2)
    engine = AutoencoderEngine(config=config)
    
    engine.fit(df_nan)
    results = engine.predict(df_nan)
    
    assert len(results) == len(df_nan)
    assert not results["anomaly_score"].isna().any()

def test_save_load(sample_data, tmp_path):
    config = AutoencoderConfig(epochs=2, hidden_dims=(8, 4, 8))
    engine = AutoencoderEngine(config=config)
    engine.fit(sample_data)
    
    engine.save(tmp_path)
    
    assert (tmp_path / "model.pt").exists()
    assert (tmp_path / "imputer.joblib").exists()
    assert (tmp_path / "scaler.joblib").exists()
    assert (tmp_path / "state.json").exists()
    
    engine2 = AutoencoderEngine.load(tmp_path)
    assert engine2.is_fitted
    assert engine2.features == engine.features
    
    # Calculate predictions on both
    pred1 = engine.calculate_reconstruction_error(sample_data)
    pred2 = engine2.calculate_reconstruction_error(sample_data)
    
    np.testing.assert_array_almost_equal(pred1, pred2)
