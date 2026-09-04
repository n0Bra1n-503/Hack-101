#!/usr/bin/env python3
"""
SkyGuard AI - ML Pipeline End-to-End Verification Script

This script performs comprehensive end-to-end verification of the ML pipeline:
1. Artifact Loading Check (Isolation Forest, Autoencoder, Scalers, Imputers, Features)
2. Streaming Behavior & Rolling Window Buffer Check
3. Normal Observations Inference & Output Schema Validation
4. Controlled Fault Testing (SPIKE, DRIFT, FROZEN, DROPOUT, ABRUPT_JUMP, MULTIVARIATE)
5. DROPOUT Weakness Detailed Analysis (Strong vs Weak)
6. Missing Values Robustness Check (Missing temp, pres, hum, all)
7. Invalid Input Rejection Check (Missing timestamp, missing station_id, non-numeric, malformed)
8. Raw Data & Model Artifact Immutability Audit (SHA-256 Hashes)
9. Backend Handoff Verification
"""

import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Ensure repository root is in sys.path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.pipeline.inference_pipeline import SkyGuardInferencePipeline
from src.data.loader import load_merged_sensor_data
from src.data.schema import SensorSchema


def get_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def compute_baseline_hashes() -> Dict[str, str]:
    """Compute SHA-256 hashes of all raw data and model artifacts."""
    files_to_hash = [
        # Raw data
        Path("data/raw/temperature.csv"),
        Path("data/raw/pressure.csv"),
        Path("data/raw/humidity.csv"),
        # Step 5 injected data
        Path("data/processed/fault_injection/injected_dataset.csv"),
        Path("data/processed/fault_injection/ground_truth.csv"),
        Path("data/processed/fault_injection/fault_metadata.csv"),
        # Models
        Path("models/isolation_forest/model.joblib"),
        Path("models/autoencoder/model.pt"),
        Path("models/autoencoder/scaler.joblib"),
        Path("models/autoencoder/imputer.joblib"),
        Path("models/autoencoder/state.json"),
    ]
    hashes = {}
    for p in files_to_hash:
        if p.exists():
            hashes[str(p)] = get_file_hash(p)
    return hashes


def verify_output_schema(result: Dict[str, Any]) -> None:
    """Verify that result strictly adheres to the required output schema."""
    # Identification
    assert "identification" in result, "Missing 'identification'"
    assert "timestamp" in result["identification"], "Missing 'timestamp' in identification"
    assert "station_id" in result["identification"], "Missing 'station_id' in identification"

    # Sensor values
    assert "sensor_values" in result, "Missing 'sensor_values'"
    for sensor in ["temperature", "pressure", "humidity"]:
        assert sensor in result["sensor_values"], f"Missing '{sensor}' in sensor_values"

    # Anomaly evidence
    assert "anomaly_evidence" in result, "Missing 'anomaly_evidence'"
    for ev in ["statistical_anomaly_score", "isolation_forest_score", "autoencoder_reconstruction_error", "hybrid_anomaly_score"]:
        assert ev in result["anomaly_evidence"], f"Missing '{ev}' in anomaly_evidence"
        score = result["anomaly_evidence"][ev]
        assert not np.isnan(score) and not np.isinf(score), f"Invalid anomaly evidence value: {ev}={score}"

    # Decision evidence
    assert "decision_evidence" in result, "Missing 'decision_evidence'"
    for dev in ["sensor_fault_score", "genuine_weather_score", "evidence_conflict_score"]:
        assert dev in result["decision_evidence"], f"Missing '{dev}' in decision_evidence"
        score = result["decision_evidence"][dev]
        assert not np.isnan(score) and not np.isinf(score), f"Invalid decision evidence value: {dev}={score}"

    # Final decision
    assert "classification" in result, "Missing 'classification'"
    assert result["classification"] in ["GENUINE_WEATHER", "SENSOR_FAULT", "UNCERTAIN"], f"Invalid classification: {result['classification']}"

    # Fault type
    assert "fault_type" in result, "Missing 'fault_type'"
    valid_fault_types = ["SPIKE", "DRIFT", "FROZEN", "DROPOUT", "ABRUPT_JUMP", "MULTIVARIATE_INCONSISTENCY", "UNKNOWN", "NONE"]
    assert result["fault_type"] in valid_fault_types, f"Invalid fault_type: {result['fault_type']}"

    # Trust score
    assert "trust_score" in result, "Missing 'trust_score'"
    trust = result["trust_score"]
    assert 0.0 <= trust <= 100.0, f"Trust score out of bounds [0, 100]: {trust}"
    assert not np.isnan(trust) and not np.isinf(trust), f"Invalid trust score: {trust}"

    # Explanation
    assert "explanation" in result, "Missing 'explanation'"
    assert isinstance(result["explanation"], str) and len(result["explanation"]) > 0, "Explanation must be a non-empty string"


def run_all_verifications():
    print("=" * 70)
    print("SKYGUARD AI — END-TO-END ML PIPELINE VERIFICATION")
    print("=" * 70)

    # 0. Compute Baseline File Hashes
    baseline_hashes = compute_baseline_hashes()
    print(f"\n[INIT] Computed baseline SHA-256 hashes for {len(baseline_hashes)} files.")

    # 1. Verify Artifact Loading (Section 14)
    print("\n--- 1. ARTIFACT LOADING VERIFICATION (Section 14) ---")
    pipeline = SkyGuardInferencePipeline(models_dir="models", window_size=50)

    assert pipeline.if_engine.is_fitted, "Isolation Forest model is not fitted"
    assert pipeline.if_engine.model is not None, "Isolation Forest model object missing"
    assert len(pipeline.if_engine.features) > 0, "Isolation Forest features list empty"
    print(f"  [PASS] Isolation Forest loaded successfully ({len(pipeline.if_engine.features)} features, threshold={pipeline.if_engine.threshold:.4f})")

    assert pipeline.ae_engine.is_fitted, "Autoencoder model is not fitted"
    assert pipeline.ae_engine.model is not None, "Autoencoder model object missing"
    assert pipeline.ae_engine.scaler is not None, "Autoencoder scaler missing"
    assert pipeline.ae_engine.imputer is not None, "Autoencoder imputer missing"
    assert len(pipeline.ae_engine.features) > 0, "Autoencoder features list empty"
    print(f"  [PASS] Autoencoder loaded successfully ({len(pipeline.ae_engine.features)} features, threshold={pipeline.ae_engine.threshold:.4f})")

    assert pipeline.stat_detector is not None, "Statistical Baseline detector missing"
    print("  [PASS] Statistical baseline detector initialized successfully.")

    assert pipeline.hybrid_engine is not None, "Hybrid Evidence engine missing"
    print("  [PASS] Hybrid Evidence engine initialized successfully.")

    assert pipeline.decision_engine is not None, "Decision Engine missing"
    print("  [PASS] Decision engine initialized successfully.")

    # 2. Test Streaming Behavior & Rolling Window (Section 9)
    print("\n--- 2. STREAMING BEHAVIOR & ROLLING WINDOW CHECK (Section 9) ---")
    print(f"  Initial history buffer length: {len(pipeline._history_buffer)}")
    assert len(pipeline._history_buffer) == 0

    # Feed 3 dummy observations
    obs_seq = [
        {"timestamp": "2024-05-10 00:00:00", "station_id": "Pashan AWS", "temperature": 25.0, "pressure": 950.0, "humidity": 60.0},
        {"timestamp": "2024-05-10 00:05:00", "station_id": "Pashan AWS", "temperature": 25.1, "pressure": 950.1, "humidity": 60.2},
        {"timestamp": "2024-05-10 00:10:00", "station_id": "Pashan AWS", "temperature": 25.2, "pressure": 950.0, "humidity": 60.5},
    ]

    for i, obs in enumerate(obs_seq, 1):
        res = pipeline.update(obs)
        assert len(pipeline._history_buffer) == i, f"Expected buffer length {i}, got {len(pipeline._history_buffer)}"
        print(f"  Step {i}: buffer len={len(pipeline._history_buffer)}, class={res['classification']}, trust={res['trust_score']}")

    print("  [PASS] History buffer increments on sequential update calls.")

    # Verify that creating a new pipeline resets state
    fresh_pipeline = SkyGuardInferencePipeline(models_dir="models", window_size=50)
    assert len(fresh_pipeline._history_buffer) == 0
    print("  [PASS] Creating a new pipeline instance properly resets history buffer.")

    # 3. Test Normal Observations & Output Structure (Section 4, 5, 6)
    print("\n--- 3. NORMAL OBSERVATIONS & SCHEMA VALIDATION (Section 4, 5, 6) ---")
    df_clean = load_merged_sensor_data(data_dir="data/raw")
    pashan_clean = df_clean[df_clean["station_id"] == "Pashan AWS"].sort_values("timestamp").reset_index(drop=True)

    stream_pipeline = SkyGuardInferencePipeline(models_dir="models", window_size=50)
    normal_results = []

    # Stream 60 normal observations
    num_normal = 60
    print(f"  Streaming {num_normal} normal observations from Pashan AWS to fill rolling window...")
    for idx in range(num_normal):
        row = pashan_clean.iloc[idx]
        obs = {
            "timestamp": str(row["timestamp"]),
            "station_id": str(row["station_id"]),
            "temperature": float(row["temperature"]),
            "pressure": float(row["pressure"]),
            "humidity": float(row["humidity"])
        }
        res = stream_pipeline.update(obs)
        verify_output_schema(res)
        normal_results.append(res)

    print(f"  [PASS] Buffer capped at window_size: len(buffer) = {len(stream_pipeline._history_buffer)} (max={stream_pipeline.window_size})")
    assert len(stream_pipeline._history_buffer) == 50

    # Inspect representative normal observations
    print("\n  Representative Normal Observations Results:")
    for sample_idx in [10, 30, 55]:
        sample_res = normal_results[sample_idx]
        print(f"    Obs {sample_idx} ({sample_res['identification']['timestamp']}):")
        print(f"      Classification: {sample_res['classification']}")
        print(f"      Fault Type:     {sample_res['fault_type']}")
        print(f"      Trust Score:    {sample_res['trust_score']:.1f}")
        print(f"      Hybrid Anomaly: {sample_res['anomaly_evidence']['hybrid_anomaly_score']:.3f}")
        print(f"      Explanation:    {sample_res['explanation']}")

    # 4. Test Known Faults from Step 5 Dataset (Section 7)
    print("\n--- 4. CONTROLLED FAULT TESTING (Section 7) ---")
    df_inj = pd.read_csv("data/processed/fault_injection/injected_dataset.csv")
    df_gt = pd.read_csv("data/processed/fault_injection/ground_truth.csv")
    df_meta = pd.read_csv("data/processed/fault_injection/fault_metadata.csv")

    fault_targets = [
        ("SPIKE", "FAULT_80B4D514"),
        ("DRIFT", "FAULT_D69847DC"),
        ("FROZEN", "FAULT_705C634C"),
        ("ABRUPT_JUMP", "FAULT_B7873CA3"),
        ("MULTIVARIATE_INCONSISTENCY", "FAULT_8071D8E6"),
    ]

    fault_eval_records = []

    for ft_name, event_id in fault_targets:
        meta_row = df_meta[df_meta["event_id"] == event_id].iloc[0]
        st_id = meta_row["station_id"]
        start_idx = int(meta_row["start_idx"])
        end_idx = int(meta_row["end_idx"])

        # Dedicated pipeline for this station stream
        test_pipe = SkyGuardInferencePipeline(models_dir="models", window_size=50)

        # Feed 30 warm-up rows before the fault so rolling stats are established
        warmup_start = max(0, start_idx - 30)
        for i in range(warmup_start, start_idx):
            r = df_inj.iloc[i]
            test_pipe.update({
                "timestamp": str(r["timestamp"]),
                "station_id": str(r["station_id"]),
                "temperature": float(r["temperature"]) if not pd.isna(r["temperature"]) else None,
                "pressure": float(r["pressure"]) if not pd.isna(r["pressure"]) else None,
                "humidity": float(r["humidity"]) if not pd.isna(r["humidity"]) else None,
            })

        # Now feed the fault observations
        event_results = []
        for i in range(start_idx, end_idx + 1):
            r = df_inj.iloc[i]
            obs = {
                "timestamp": str(r["timestamp"]),
                "station_id": str(r["station_id"]),
                "temperature": float(r["temperature"]) if not pd.isna(r["temperature"]) else None,
                "pressure": float(r["pressure"]) if not pd.isna(r["pressure"]) else None,
                "humidity": float(r["humidity"]) if not pd.isna(r["humidity"]) else None,
            }
            # STRICT CHECK: Ensure NO fault metadata is in obs
            for forbidden in ["fault_type", "fault_present", "affected_sensor", "event_id"]:
                assert forbidden not in obs, f"Leakage detected: {forbidden} in observation!"

            res = test_pipe.update(obs)
            verify_output_schema(res)
            event_results.append(res)

        # Pick the most severe / representative observation within the fault event
        rep_res = max(event_results, key=lambda x: x["decision_evidence"]["sensor_fault_score"])
        fault_eval_records.append({
            "fault": ft_name,
            "event_id": event_id,
            "station": st_id,
            "sensor": meta_row["sensor"],
            "rep_result": rep_res
        })

        print(f"\n  Actual injected fault:    {ft_name} (Event: {event_id}, Sensor: {meta_row['sensor']})")
        print(f"  Predicted classification: {rep_res['classification']}")
        print(f"  Predicted fault type:     {rep_res['fault_type']}")
        print(f"  Trust score:              {rep_res['trust_score']:.1f}")
        print(f"  Hybrid anomaly score:     {rep_res['anomaly_evidence']['hybrid_anomaly_score']:.3f}")
        print(f"  Sensor fault score:       {rep_res['decision_evidence']['sensor_fault_score']:.3f}")
        print(f"  Explanation:              {rep_res['explanation']}")

    # 5. Specifically Test the DROPOUT Weakness (Section 8)
    print("\n--- 5. DROPOUT WEAKNESS DETAILED ANALYSIS (Section 8) ---")
    # Strong DROPOUT vs Weaker DROPOUT cases
    # We saw in ground truth:
    # Event FAULT_0C3AFA91 (Pashan AWS, temperature): duration 12 rows
    # Event FAULT_DC4A477D (Shivajinagar AWS, pressure): duration 7 rows
    dropout_cases = [
        ("Strong / Long DROPOUT", "FAULT_0C3AFA91", "Pashan AWS"),
        ("Moderate DROPOUT", "FAULT_DC4A477D", "Shivajinagar AWS"),
    ]

    for label, event_id, st_id in dropout_cases:
        meta_row = df_meta[df_meta["event_id"] == event_id].iloc[0]
        start_idx = int(meta_row["start_idx"])
        end_idx = int(meta_row["end_idx"])

        pipe_do = SkyGuardInferencePipeline(models_dir="models", window_size=50)

        # Warm-up
        warmup_start = max(0, start_idx - 25)
        for i in range(warmup_start, start_idx):
            r = df_inj.iloc[i]
            pipe_do.update({
                "timestamp": str(r["timestamp"]),
                "station_id": str(r["station_id"]),
                "temperature": float(r["temperature"]) if not pd.isna(r["temperature"]) else None,
                "pressure": float(r["pressure"]) if not pd.isna(r["pressure"]) else None,
                "humidity": float(r["humidity"]) if not pd.isna(r["humidity"]) else None,
            })

        do_results = []
        for i in range(start_idx, end_idx + 1):
            r = df_inj.iloc[i]
            obs = {
                "timestamp": str(r["timestamp"]),
                "station_id": str(r["station_id"]),
                "temperature": float(r["temperature"]) if not pd.isna(r["temperature"]) else None,
                "pressure": float(r["pressure"]) if not pd.isna(r["pressure"]) else None,
                "humidity": float(r["humidity"]) if not pd.isna(r["humidity"]) else None,
            }
            res = pipe_do.update(obs)
            verify_output_schema(res)
            do_results.append(res)

        print(f"\n  Case: {label} (Event: {event_id}, Sensor: {meta_row['sensor']}, Duration: {end_idx - start_idx + 1} steps)")
        classes = [r["classification"] for r in do_results]
        trusts = [r["trust_score"] for r in do_results]
        ae_scores = [r["anomaly_evidence"]["autoencoder_reconstruction_error"] for r in do_results]
        print(f"    Classifications: {classes}")
        print(f"    Trust scores:    Min={min(trusts):.1f}, Max={max(trusts):.1f}, Mean={np.mean(trusts):.1f}")
        print(f"    AE Reconstruction Errors: Min={min(ae_scores):.3f}, Max={max(ae_scores):.3f}")
        print(f"    Representative Explanation: {do_results[len(do_results)//2]['explanation']}")

    # 6. Test Missing Values (Section 10)
    print("\n--- 6. MISSING VALUES ROBUSTNESS (Section 10) ---")
    missing_test_cases = [
        ("Missing temperature", {"timestamp": "2024-05-15 12:00:00", "station_id": "Pashan AWS", "temperature": None, "pressure": 950.2, "humidity": 55.4}),
        ("Missing pressure", {"timestamp": "2024-05-15 12:05:00", "station_id": "Pashan AWS", "temperature": 28.5, "pressure": None, "humidity": 55.4}),
        ("Missing humidity", {"timestamp": "2024-05-15 12:10:00", "station_id": "Pashan AWS", "temperature": 28.5, "pressure": 950.2, "humidity": None}),
        ("Multiple missing (all sensors)", {"timestamp": "2024-05-15 12:15:00", "station_id": "Pashan AWS", "temperature": None, "pressure": None, "humidity": None}),
    ]

    pipe_missing = SkyGuardInferencePipeline(models_dir="models", window_size=50)
    for desc, obs in missing_test_cases:
        res = pipe_missing.update(obs)
        verify_output_schema(res)
        print(f"  [PASS] {desc:32s} -> Class: {res['classification']:14s} | FaultType: {res['fault_type']:10s} | Trust: {res['trust_score']:.1f}")

    # 7. Test Invalid Inputs (Section 11)
    print("\n--- 7. INVALID INPUT REJECTION (Section 11) ---")
    invalid_cases = [
        ("Missing required timestamp", {"station_id": "STA_1", "temperature": 25.0, "pressure": 1013.25, "humidity": 50.0}, ValueError),
        ("Malformed timestamp string", {"timestamp": "invalid_date_xyz", "station_id": "STA_1", "temperature": 25.0, "pressure": 1013.25, "humidity": 50.0}, ValueError),
        ("Missing station ID", {"timestamp": "2024-05-15 12:00:00", "temperature": 25.0, "pressure": 1013.25, "humidity": 50.0}, ValueError),
        ("Non-numeric temperature", {"timestamp": "2024-05-15 12:00:00", "station_id": "STA_1", "temperature": "hot", "pressure": 1013.25, "humidity": 50.0}, ValueError),
        ("Non-numeric pressure", {"timestamp": "2024-05-15 12:00:00", "station_id": "STA_1", "temperature": 25.0, "pressure": "high", "humidity": 50.0}, ValueError),
        ("Non-numeric humidity", {"timestamp": "2024-05-15 12:00:00", "station_id": "STA_1", "temperature": 25.0, "pressure": 1013.25, "humidity": "humid", "object": {}}, ValueError),
    ]

    pipe_invalid = SkyGuardInferencePipeline(models_dir="models", window_size=50)
    for desc, bad_obs, expected_err in invalid_cases:
        try:
            pipe_invalid.update(bad_obs)
            assert False, f"Expected {expected_err.__name__} for '{desc}', but update() succeeded!"
        except expected_err as e:
            print(f"  [PASS] Successfully rejected: {desc} ({expected_err.__name__}: {e})")

    # 8. Raw Data & Model Artifact Immutability Audit (Section 12, 13)
    print("\n--- 8. DATA SAFETY & RETRAINING AUDIT (Section 12, 13) ---")
    post_hashes = compute_baseline_hashes()
    assert len(baseline_hashes) == len(post_hashes), "File count mismatch after inference"

    for file_path, base_h in baseline_hashes.items():
        post_h = post_hashes[file_path]
        assert base_h == post_h, f"CRITICAL: File {file_path} was modified during inference! ({base_h} vs {post_h})"
        print(f"  [PASS] Immutable: {file_path}")

    # 9. Backend Handoff Verification (Section 15)
    print("\n--- 9. BACKEND HANDOFF VERIFICATION (Section 15) ---")
    handoff_obs = {
        "timestamp": "2024-05-18T14:30:00Z",
        "station_id": "Pashan AWS",
        "temperature": 29.4,
        "pressure": 952.1,
        "humidity": 62.0
    }
    handoff_pipe = SkyGuardInferencePipeline(models_dir="models", window_size=50)
    handoff_res = handoff_pipe.update(handoff_obs)
    verify_output_schema(handoff_res)
    print("  [PASS] Backend handoff usage test succeeded.")
    print("  Sample output structure verified:")
    import json
    # Convert any non-serializable items if needed
    print(json.dumps(handoff_res, indent=4))

    print("\n" + "=" * 70)
    print("ALL END-TO-END VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_verifications()
