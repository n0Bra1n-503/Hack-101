# SkyGuard AI - ML Integration Guide

This document describes how the backend team can integrate the SkyGuard AI ML Inference Pipeline into the final application.

## Overview
The ML Pipeline processes Automatic Weather Station (AWS) sensor data to identify anomalies, classify them as either `GENUINE_WEATHER` or `SENSOR_FAULT` (or `UNCERTAIN`), and assigns a `trust_score` (0-100). 

It is completely decoupled from the database, web server, and API. It provides a pure Python interface.

## Quick Start (Python Interface)

### 1. Import the pipeline

```python
from src.pipeline.inference_pipeline import SkyGuardInferencePipeline

# Initialize the pipeline once at application startup.
# This loads all pre-trained models into memory and maintains a sliding window buffer.
pipeline = SkyGuardInferencePipeline(models_dir="models", window_size=50)
```

### 2. Run inference on a single observation (Streaming)

```python
# Raw observation from your database or MQTT stream
raw_obs = {
    "timestamp": "2024-01-01T12:00:00Z",
    "station_id": "STATION_ALPHA",
    "temperature": 22.5,
    "pressure": 1012.1,
    "humidity": 45.0
}

# The pipeline updates its internal temporal buffer and returns the decision for this row
result = pipeline.update(raw_obs)
print(result["classification"])  # e.g., "GENUINE_WEATHER"
print(result["trust_score"])     # e.g., 100.0
```

## Required Input Schema
The `update()` method expects a dictionary with at least the following keys:
- `timestamp` (String/Datetime)
- `station_id` (String)
- `temperature` (Float)
- `pressure` (Float)
- `humidity` (Float)

## Output Schema
The dictionary returned by `update()` matches this exact structure:

```json
{
  "identification": {
    "timestamp": "2024-01-01T12:00:00Z",
    "station_id": "STATION_ALPHA"
  },
  "sensor_values": {
    "temperature": 22.5,
    "pressure": 1012.1,
    "humidity": 45.0
  },
  "anomaly_evidence": {
    "statistical_anomaly_score": 0.05,
    "isolation_forest_score": 0.02,
    "autoencoder_reconstruction_error": 0.01,
    "hybrid_anomaly_score": 0.03
  },
  "decision_evidence": {
    "sensor_fault_score": 0.01,
    "genuine_weather_score": 0.15,
    "evidence_conflict_score": 0.02
  },
  "classification": "GENUINE_WEATHER",
  "fault_type": "NONE",
  "trust_score": 100.0,
  "explanation": "Behavior appears normal and consistent."
}
```

## Limitations & Notes for Backend Developers
1. **Temporal Context:** The `update()` method is stateful. It keeps the last N observations in memory to calculate rolling deviations. If your backend is load-balanced across multiple workers, ensure that data for the same `station_id` routes to the same pipeline instance, or pass large batches to `predict_batch()` instead.
2. **Missing Values:** The models handle `None` or `NaN` inputs gracefully by imputing them based on historical medians, but extreme missingness will drastically reduce the `trust_score`.
3. **Reproducing Evaluations:** To run the full ML evaluation pipeline to verify metrics locally, run `.venv/bin/python src/pipeline/run_full_evaluation.py`.
