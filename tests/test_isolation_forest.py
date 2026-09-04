import pytest
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema
from src.models.isolation_forest import IsolationForestEngine, get_isolation_forest_features
from src.models.config import IsolationForestConfig
import joblib

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
    features = get_isolation_forest_features(sample_data)
    
    # Ground truth shouldn't be here
    assert "fault_present" not in features
    assert "fault_type" not in features
    
    # Metadata shouldn't be here
    assert "station_id" not in features
    assert "timestamp" not in features
    
    # Core sensors should be here
    assert "temperature" in features
    assert "pressure" in features
    assert "humidity" in features

def test_engine_fit_predict(sample_data):
    config = IsolationForestConfig(random_state=42, n_estimators=10)
    engine = IsolationForestEngine(config=config)
    
    # Train
    engine.fit(sample_data)
    assert engine.is_fitted
    assert len(engine.features) == 3
    
    # Predict
    results = engine.predict(sample_data)
    assert "anomaly_score" in results.columns
    assert "anomaly_prediction" in results.columns
    
    # In sklearn isolation forest, decision function returns negative for outliers
    # We inverted it, so outliers are more positive
    # Check that boolean predictions align with threshold
    manual_preds = results["anomaly_score"] >= engine.threshold
    pd.testing.assert_series_equal(results["anomaly_prediction"], manual_preds, check_names=False)

def test_missing_data_imputation(sample_data):
    # Introduce NaNs
    df_nan = sample_data.copy()
    df_nan.loc[0, "temperature"] = np.nan
    df_nan.loc[1, "pressure"] = np.nan
    
    config = IsolationForestConfig(n_estimators=5)
    engine = IsolationForestEngine(config=config)
    
    # Should not crash on NaNs because imputer is present
    engine.fit(df_nan)
    results = engine.predict(df_nan)
    
    assert len(results) == len(df_nan)
    assert not results["anomaly_score"].isna().any()

def test_save_load(sample_data, tmp_path):
    config = IsolationForestConfig(random_state=1)
    engine = IsolationForestEngine(config=config)
    engine.fit(sample_data)
    
    path = tmp_path / "model.joblib"
    engine.save(path)
    
    assert path.exists()
    
    engine2 = IsolationForestEngine.load(path)
    assert engine2.is_fitted
    assert engine2.features == engine.features
    assert engine2.config.random_state == 1
    
    # Predictions should be identical
    pred1 = engine.predict(sample_data)
    pred2 = engine2.predict(sample_data)
    pd.testing.assert_frame_equal(pred1, pred2)
