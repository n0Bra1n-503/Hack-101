# SkyGuard AI — Inter-Module Data Contracts

## Overview

This document specifies the authoritative data exchange formats across SkyGuard AI system components. It defines the formal boundaries between **Data Collection (Neha)**, **ML Anomaly Detection (Manan)**, **Decision Intelligence & Backend Integration (Mitali)**, and **Visual Analytics & Frontend (Medhvi & Darshita)**.

All services must serialize, validate, and consume payloads conforming strictly to these schemas.

---

## 1. Weather Reading Ingestion Contract

### Source
* Emitted by Automated Weather Stations (AWS), raw data collectors, or historical replay pipelines.
* Consumed by FastAPI backend ingestion (`/api/readings`) and the ML Anomaly Adapter.

### JSON Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WeatherReading",
  "type": "object",
  "required": ["station_id", "timestamp", "temperature", "pressure", "humidity"],
  "properties": {
    "station_id": {
      "type": "string",
      "description": "Unique identifier of the automated weather station."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Observation timestamp in ISO 8601 UTC format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
    },
    "temperature": {
      "type": "number",
      "description": "Ambient temperature in degrees Celsius (°C)."
    },
    "pressure": {
      "type": "number",
      "description": "Atmospheric pressure in hectopascals (hPa)."
    },
    "humidity": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 100.0,
      "description": "Relative humidity percentage (%)."
    }
  }
}
```

### Canonical Payload Example
```json
{
  "station_id": "AWS-104",
  "timestamp": "2026-09-04T10:00:00",
  "temperature": 31.2,
  "pressure": 1004.1,
  "humidity": 48.2
}
```

---

## 2. ML Anomaly Detection Contract

### Source
* Emitted by Manan's ML Anomaly Detection models (Statistical, Isolation Forest, Autoencoder, or Hybrid).
* Consumed by Mitali's `ml/integration/` adapter.

### JSON Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AnomalyResult",
  "type": "object",
  "required": ["anomaly", "anomaly_score", "signals"],
  "properties": {
    "anomaly": {
      "type": "boolean",
      "description": "True if any detector flags this observation as an anomaly."
    },
    "anomaly_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Normalized ensemble anomaly likelihood score between 0.0 and 1.0."
    },
    "signals": {
      "type": "object",
      "description": "Sub-model individual scoring breakdown.",
      "properties": {
        "statistical": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Z-score / rolling-quantile anomaly score."
        },
        "isolation_forest": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Isolation Forest normalized anomaly score."
        },
        "autoencoder": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Reconstruction error anomaly score from deep autoencoder."
        }
      },
      "required": ["statistical", "isolation_forest", "autoencoder"]
    }
  }
}
```

### Canonical Payload Example
```json
{
  "anomaly": true,
  "anomaly_score": 0.94,
  "signals": {
    "statistical": 0.91,
    "isolation_forest": 0.96,
    "autoencoder": 0.95
  }
}
```

---

## 3. Decision Engine Contract

### Source
* Produced by Mitali's `reasoning_service.py`.
* Consumed by `trust_service.py`, `fault_classifier.py`, and `explanation_service.py`.

### JSON Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DecisionResult",
  "type": "object",
  "required": ["decision", "confidence", "evidence"],
  "properties": {
    "decision": {
      "type": "string",
      "enum": ["genuine_weather", "sensor_fault", "uncertain"],
      "description": "Categorical root cause determination."
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Statistical confidence in the decision."
    },
    "evidence": {
      "type": "object",
      "description": "Breakdown of corroborating and refuting evidence scores (0.0 to 1.0).",
      "properties": {
        "temporal": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Temporal plausibility score based on rate of change and trend."
        },
        "cross_sensor": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Thermodynamic consistency score across co-located sensors."
        },
        "cross_station": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Spatial consistency score relative to neighboring stations."
        },
        "persistence": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Historical persistence metric over rolling time windows."
        }
      },
      "required": ["temporal", "cross_sensor", "cross_station", "persistence"]
    }
  }
}
```

### Canonical Payload Example
```json
{
  "decision": "sensor_fault",
  "confidence": 0.97,
  "evidence": {
    "temporal": 0.95,
    "cross_sensor": 0.92,
    "cross_station": 0.98,
    "persistence": 0.88
  }
}
```

---

## 4. Final Evaluation Result Contract

### Source
* Emitted by Mitali's inference pipeline (REST API `/api/inference/{reading_id}` and real-time WebSocket feed).
* Consumed by frontend dashboards (Darshita/Medhvi), downstream client systems, and maintenance workflows.

### JSON Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FinalEvaluationResult",
  "type": "object",
  "required": [
    "reading_id",
    "decision",
    "fault_type",
    "trust_score",
    "confidence",
    "suggested_value",
    "explanation"
  ],
  "properties": {
    "reading_id": {
      "type": "string",
      "description": "Unique identifier of the evaluated reading."
    },
    "decision": {
      "type": "string",
      "enum": ["genuine_weather", "sensor_fault", "uncertain"],
      "description": "Final operational classification."
    },
    "fault_type": {
      "type": ["string", "null"],
      "enum": [
        "temperature_spike",
        "temperature_drift",
        "frozen_sensor",
        "dropout",
        "abrupt_jump",
        "bias",
        "noise",
        "multivariate_inconsistency",
        null
      ],
      "description": "Identified fault archetype (null if genuine_weather or unclassified)."
    },
    "trust_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Calibrated reliability metric for downstream consumers."
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Overall confidence score."
    },
    "suggested_value": {
      "type": ["number", "null"],
      "description": "Imputed replacement value (null if genuine_weather)."
    },
    "explanation": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Transparent bullet points explaining the decision rationale."
    }
  }
}
```

### Canonical Payload Example
```json
{
  "reading_id": "R123",
  "decision": "sensor_fault",
  "fault_type": "temperature_spike",
  "trust_score": 18,
  "confidence": 0.97,
  "suggested_value": 31.8,
  "explanation": [
    "Temperature jumped sharply",
    "Nearby stations remained around 31–32°C",
    "Humidity and pressure did not support the spike"
  ]
}
```
