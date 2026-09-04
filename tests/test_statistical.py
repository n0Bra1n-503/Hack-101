import json
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from src.data.schema import SensorSchema
from src.statistical.config import StatisticalConfig
from src.statistical.baselines import (
    SensorStatRecord,
    fit_statistical_baselines,
)
from src.statistical.scoring import (
    compute_standardized_scores,
    calculate_statistical_scores,
)
from src.statistical.evidence import extract_statistical_evidence
from src.statistical.detector import (
    StatisticalBaselineDetector,
    detect_statistical_anomalies,
)
from src.statistical.summary import generate_statistical_summary


@pytest.fixture
def schema():
    return SensorSchema()


@pytest.fixture
def sample_station_df(schema):
    """Create a controlled in-memory DataFrame with known properties for testing."""
    np.random.seed(42)
    stations = ["STN_A", "STN_B"]
    base_time = datetime(2026, 1, 1, 0, 0, 0)
    records = []

    for stn in stations:
        # Station A baseline: temp ~20, press ~1013, humid ~50
        # Station B baseline: temp ~30, press ~1005, humid ~70
        t_base = 20.0 if stn == "STN_A" else 30.0
        p_base = 1013.0 if stn == "STN_A" else 1005.0
        h_base = 50.0 if stn == "STN_A" else 70.0

        for i in range(48):  # 48 points, 30 min intervals (24 hours)
            dt = base_time + timedelta(minutes=30 * i)
            hour_val = dt.hour
            # Diurnal swing
            t_val = t_base + np.sin(2 * np.pi * hour_val / 24.0) * 5.0 + np.random.normal(0, 0.5)
            p_val = p_base + np.random.normal(0, 0.5)
            h_val = h_base - np.sin(2 * np.pi * hour_val / 24.0) * 10.0 + np.random.normal(0, 1.0)

            records.append({
                schema.station_id: stn,
                schema.timestamp: dt.isoformat(),
                schema.hour: hour_val,
                schema.temperature: t_val,
                schema.pressure: p_val,
                schema.humidity: h_val,
            })

    df = pd.DataFrame(records)
    return df


def test_sensor_stat_record_calculation():
    """Test standard and robust statistical measures on a clean series."""
    vals = pd.Series([10.0, 12.0, 11.0, 10.5, 11.5, 100.0])  # One extreme outlier
    stat = SensorStatRecord.from_series(vals)

    assert stat.count == 6
    assert stat.mean > 20.0  # Mean is skewed by 100.0
    assert 10.5 <= stat.median <= 11.5  # Median remains robust
    assert stat.iqr > 0
    assert stat.mad > 0


def test_zero_std_handling():
    """Test that zero variance / constant values do not produce divide-by-zero or NaNs."""
    constant_vals = pd.Series([25.0, 25.0, 25.0, 25.0, 25.0])
    stat = SensorStatRecord.from_series(constant_vals)
    assert stat.std == 0.0
    assert stat.iqr == 0.0

    # Normal observation equal to constant mean
    z, rob = compute_standardized_scores(pd.Series([25.0]), stat)
    assert z.iloc[0] == 0.0
    assert rob.iloc[0] == 0.0

    # Outlier observation differing from constant mean
    z_out, rob_out = compute_standardized_scores(pd.Series([30.0]), stat)
    assert z_out.iloc[0] > 10.0  # Safe extreme score without inf/nan
    assert rob_out.iloc[0] > 10.0


def test_nan_and_inf_handling(schema):
    """Test robust handling of missing and infinite input data."""
    df_edge = pd.DataFrame({
        schema.station_id: ["STN_A", "STN_A", "STN_A", "STN_A"],
        schema.timestamp: ["2026-01-01T00:00:00", "2026-01-01T01:00:00", "2026-01-01T02:00:00", "2026-01-01T03:00:00"],
        schema.hour: [0, 1, 2, 3],
        schema.temperature: [20.0, np.nan, 22.0, 21.0],
        schema.pressure: [1013.0, 1014.0, np.inf, 1013.5],
        schema.humidity: [50.0, 52.0, 51.0, -np.inf],
    })

    detector = StatisticalBaselineDetector(schema=schema)
    results = detector.fit_transform(df_edge)

    # Ensure pipeline executed and produced valid output shapes
    assert len(results) == len(df_edge)
    assert "statistical_anomaly_score" in results.columns
    assert "reasons" in results.columns

    # No unhandled infinite scores in computed score columns
    score_cols = [c for c in results.select_dtypes(include=[np.number]).columns if c not in schema.required_sensor_columns]
    for col in score_cols:
        assert not np.isinf(results[col]).any(), f"Infinite value found in output column {col}"


def test_station_specific_baselines(sample_station_df, schema):
    """Test that station-specific baselines properly isolate station distributions."""
    detector = StatisticalBaselineDetector(schema=schema)
    detector.fit(sample_station_df)

    # STN_A temp baseline is around 20, STN_B temp baseline is around 30
    stat_a = detector.baselines.station_stats[schema.temperature]["STN_A"]
    stat_b = detector.baselines.station_stats[schema.temperature]["STN_B"]

    assert 18.0 <= stat_a.mean <= 22.0
    assert 28.0 <= stat_b.mean <= 32.0


def test_anomaly_injection_and_detection(sample_station_df, schema):
    """Inject extreme values into a copy and verify they are flagged with clear reasons."""
    df_test = sample_station_df.copy()

    # Inject extreme temperature anomaly at row 10
    target_idx = 10
    df_test.loc[target_idx, schema.temperature] = 85.0  # Extreme high temperature

    config = StatisticalConfig(zscore_threshold=3.0, robust_threshold=3.5)
    detector = StatisticalBaselineDetector(config=config, schema=schema)
    results = detector.fit_transform(df_test)

    flagged_row = results.loc[target_idx]

    assert flagged_row["is_statistically_suspicious"] == True
    assert flagged_row["temperature_unusual"] == True
    assert flagged_row["temperature_zscore"] > 3.0
    assert flagged_row["statistical_anomaly_score"] >= config.suspicious_score_threshold
    assert flagged_row["anomaly_severity"] in ["SLIGHTLY_UNUSUAL", "STRONGLY_UNUSUAL"]

    # Reasons should be a valid JSON array of strings mentioning Temperature
    reasons = json.loads(flagged_row["reasons"])
    assert len(reasons) > 0
    assert any("Temperature" in r for r in reasons)


def test_evidence_flags_and_scoring(sample_station_df, schema):
    """Verify evidence flags, counts, and anomaly score bounds."""
    results = detect_statistical_anomalies(sample_station_df, schema=schema)

    # Score bounded between 0 and 1
    scores = results["statistical_anomaly_score"]
    assert (scores >= 0.0).all()
    assert (scores <= 1.0).all()

    # Evidence count is non-negative integer
    assert (results["evidence_count"] >= 0).all()

    # Severity levels are valid
    valid_severities = {"NORMAL", "SLIGHTLY_UNUSUAL", "STRONGLY_UNUSUAL"}
    assert set(results["anomaly_severity"].unique()).issubset(valid_severities)


def test_summary_generation(sample_station_df, schema):
    """Test that summary report dataframe calculates valid percentages and metrics."""
    results = detect_statistical_anomalies(sample_station_df, schema=schema)
    summary = generate_statistical_summary(results, schema=schema)

    assert len(summary) > 0
    metrics = set(summary["metric"])
    assert "total_observations_analyzed" in metrics
    assert "statistically_suspicious_count" in metrics
    assert "statistically_suspicious_pct" in metrics
    assert "flagged_by_temperature" in metrics
