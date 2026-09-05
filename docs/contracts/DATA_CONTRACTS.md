# SkyGuard AI — Inter-Module Data Contracts

## Overview

This document specifies the authoritative data exchange formats across SkyGuard AI system components. It defines the formal boundaries between **Data Collection (Neha)**, **ML Anomaly Detection & Risk Modeling (Manan)**, **ML Dataset Engineering & Fault Injection (Muskan)**, **Decision Intelligence, Backend Integration & Risk Integration (Mitali)**, and **Visual Analytics & Frontend (Medhvi & Darshita)**.

All services must serialize, validate, and consume payloads conforming strictly to these schemas.

---

## 1. Weather Reading Ingestion Contract

### Source
* Emitted by Automated Weather Stations (AWS), raw data collectors (Neha), or historical replay pipelines.
* Consumed by FastAPI backend ingestion (`/api/readings`) and the ML Anomaly Adapter.

### JSON Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WeatherReading",
  "type": "object",
  "required": [
    "reading_id",
    "station_id",
    "timestamp",
    "temperature",
    "pressure",
    "humidity",
    "wind_speed",
    "wind_direction",
    "rainfall",
    "solar_radiation",
    "latitude",
    "longitude",
    "area",
    "elevation",
    "source",
    "quality_flag"
  ],
  "properties": {
    "reading_id": {
      "type": "string",
      "description": "Unique identifier of the weather observation reading."
    },
    "station_id": {
      "type": "string",
      "description": "Unique identifier of the reporting automated weather station."
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
    },
    "wind_speed": {
      "type": "number",
      "minimum": 0.0,
      "description": "Wind speed in meters per second (m/s)."
    },
    "wind_direction": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 360.0,
      "description": "Wind direction in degrees from true north (0–360°)."
    },
    "rainfall": {
      "type": "number",
      "minimum": 0.0,
      "description": "Precipitation accumulation in millimeters (mm)."
    },
    "solar_radiation": {
      "type": "number",
      "minimum": 0.0,
      "description": "Solar irradiance in Watts per square meter (W/m²)."
    },
    "latitude": {
      "type": "number",
      "minimum": -90.0,
      "maximum": 90.0,
      "description": "Latitude of reporting station in decimal degrees."
    },
    "longitude": {
      "type": "number",
      "minimum": -180.0,
      "maximum": 180.0,
      "description": "Longitude of reporting station in decimal degrees."
    },
    "area": {
      "type": "string",
      "description": "Administrative or regional geographic zone."
    },
    "elevation": {
      "type": "number",
      "description": "Station elevation above sea level in meters."
    },
    "source": {
      "type": "string",
      "description": "Origin of the telemetry stream (e.g., 'weather_source', 'imd_aws', 'historical_replay', 'dummy')."
    },
    "quality_flag": {
      "type": "string",
      "description": "Initial data quality indicator (e.g., 'valid', 'suspect', 'nominal')."
    }
  }
}
```

### Canonical Payload Example
```json
{
  "reading_id": "R123",
  "station_id": "AWS-104",
  "timestamp": "2026-09-04T10:00:00",
  "temperature": 31.2,
  "pressure": 1004.1,
  "humidity": 48.2,
  "wind_speed": 12.4,
  "wind_direction": 220,
  "rainfall": 0.0,
  "solar_radiation": 650.0,
  "latitude": 28.61,
  "longitude": 77.21,
  "area": "Delhi",
  "elevation": 216.0,
  "source": "weather_source",
  "quality_flag": "valid"
}
```

---

## 2. Sensor Metadata Contract

### Source
* Emitted by station hardware registries or telemetry configuration files.
* Consumed by Digital Twin services, maintenance queues, and sensor health tracking.

### Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SensorMetadata",
  "type": "object",
  "required": [
    "sensor_id",
    "station_id",
    "sensor_type",
    "installation_date",
    "last_calibration_date",
    "status"
  ],
  "properties": {
    "sensor_id": {
      "type": "string",
      "description": "Unique identifier of the physical sensor unit."
    },
    "station_id": {
      "type": "string",
      "description": "Station where the sensor is mounted."
    },
    "sensor_type": {
      "type": "string",
      "enum": ["temperature", "barometer", "hygrometer", "anemometer", "rain_gauge", "pyranometer"],
      "description": "Physical observation type measured by the sensor."
    },
    "installation_date": {
      "type": "string",
      "format": "date",
      "description": "Date when sensor was commissioned (YYYY-MM-DD)."
    },
    "last_calibration_date": {
      "type": "string",
      "format": "date",
      "description": "Date of latest certified laboratory/field calibration (YYYY-MM-DD)."
    },
    "status": {
      "type": "string",
      "enum": ["active", "degraded", "faulty", "maintenance", "offline"],
      "description": "Current operational hardware status."
    }
  }
}
```

### Canonical Payload Example
```json
{
  "sensor_id": "SNS-TMP-104",
  "station_id": "AWS-104",
  "sensor_type": "temperature",
  "installation_date": "2024-03-15",
  "last_calibration_date": "2026-01-10",
  "status": "active"
}
```

---

## 3. Station Neighbour Relationship Contract

### Source
* Stored in static network topology (`station_neighbors.csv`) or spatial geospatial index.
* Consumed by cross-station consistency checks in Mitali's decision engine.

### Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "StationNeighbor",
  "type": "object",
  "required": ["station_id", "neighbor_id", "distance_km"],
  "properties": {
    "station_id": {
      "type": "string",
      "description": "Reference weather station identifier."
    },
    "neighbor_id": {
      "type": "string",
      "description": "Neighboring station identifier within spatial correlation radius."
    },
    "distance_km": {
      "type": "number",
      "minimum": 0.0,
      "description": "Geodesic distance between stations in kilometers."
    }
  }
}
```

### Canonical Payload Example
```json
{
  "station_id": "AWS-104",
  "neighbor_id": "AWS-105",
  "distance_km": 14.8
}
```

---

## 4. ML Anomaly Detection Contract

### Source
* Emitted by Manan's ML Anomaly Detection models (Statistical, Isolation Forest, Autoencoder, or Hybrid).
* Consumed by Mitali's `ml/integration/` adapter.

### Design Boundary
* Backend routes must never depend on specific ML library implementation details.
* The interaction occurs via an adapter abstraction:
  `result = inference_service.predict(reading, context)`
* The underlying model architecture can evolve without modifying backend service interfaces.

### JSON Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AnomalyResult",
  "type": "object",
  "required": ["anomaly", "anomaly_score", "model", "signals"],
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
    "model": {
      "type": "string",
      "description": "Model architecture generating the prediction (e.g., 'hybrid', 'isolation_forest', 'autoencoder', 'statistical')."
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
  "model": "hybrid",
  "signals": {
    "statistical": 0.91,
    "isolation_forest": 0.96,
    "autoencoder": 0.95
  }
}
```

---

## 5. Decision Engine Contract

### Source
* Produced by Mitali's `reasoning_service.py`.
* Consumed by `trust_service.py`, `fault_classifier.py`, and `explanation_service.py`.

### Allowed Decision States
1. `genuine_weather`: Confirmed authentic atmospheric phenomenon corroborated across physical dimensions.
2. `sensor_fault`: Telemetry failure attributed to sensor hardware, calibration, or electronic error.
3. `uncertain`: Inconclusive or conflicting evidence requiring operator inspection.

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
          "description": "Temporal plausibility score based on rate of change and diurnal trend."
        },
        "cross_sensor": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Thermodynamic consistency score across co-located sensors on the same station."
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
          "description": "Historical persistence metric over rolling observation windows."
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

## 6. Operational Reliability vs. Anomaly Rarity (Trust Score Principle)

### Core Invariant
> **`anomaly_score != trust_score`**
>
> The Trust Score is NOT `(100 - anomaly_score * 100)`.

* **Anomaly Score ($0.0 \to 1.0$)**: Measures *statistical rarity*. An extreme tropical cyclone or flash heatwave produces a very high anomaly score ($>0.95$).
* **Trust Score ($0 \to 100$)**: Measures *operational dependability*. When multiple independent stations and physical relationships confirm the cyclone, its readings are authentic and receive a high Trust Score ($>90$). Conversely, a stuck pin produces an anomaly with zero cross-station consensus, yielding a low Trust Score ($<20$).

---

## 7. Final Reliability Result Contract

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

---

## 8. Value Correction & Non-Destructive Ingestion Contract

### Source
* Generated by Mitali's `correction_service.py` upon determination of `sensor_fault`.
* Reviewed and managed by operators via review endpoints (`/api/corrections/{id}/accept`, `/reject`, `/review`).

### Immutability Principle
* Raw weather observations must **NEVER** be overwritten, modified, or deleted in place.
* Corrections are persisted in a separate `corrections` entity referencing the immutable raw reading.
* Correction lifecycle: `SUGGESTED` $\to$ `PENDING_REVIEW` $\to$ `ACCEPTED` / `REJECTED`.

### Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ValueCorrection",
  "type": "object",
  "required": [
    "correction_id",
    "reading_id",
    "original_value",
    "suggested_value",
    "reason",
    "confidence",
    "review_status"
  ],
  "properties": {
    "correction_id": {
      "type": "string",
      "description": "Unique identifier of the proposed correction."
    },
    "reading_id": {
      "type": "string",
      "description": "Reference to the original immutable reading."
    },
    "original_value": {
      "type": "number",
      "description": "Faulty reading value as reported by the sensor."
    },
    "suggested_value": {
      "type": "number",
      "description": "Imputed estimate derived from spatial neighbors and temporal interpolation."
    },
    "reason": {
      "type": "string",
      "description": "Automated justification for the suggested replacement."
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Confidence score of the imputation."
    },
    "review_status": {
      "type": "string",
      "enum": ["SUGGESTED", "PENDING_REVIEW", "ACCEPTED", "REJECTED"],
      "description": "Current lifecycle review state."
    },
    "reviewed_by": {
      "type": ["string", "null"],
      "description": "Operator identifier who approved or rejected the correction."
    },
    "reviewed_at": {
      "type": ["string", "null"],
      "format": "date-time",
      "description": "Timestamp of human review action."
    }
  }
}
```

---

## 9. Validated Weather Event Contract

### Source
* Extracted by Mitali's pipeline **only after** a reading successfully passes reliability verification as `genuine_weather`.
* Consumed by Manan's Disaster Risk Model adapter.

### Critical Safety Gate
* **Only validated genuine events can enter risk assessment.**
* If `decision == "sensor_fault"` $\to$ **NO disaster event is created.**
* If `decision == "uncertain"` $\to$ **NO automatic public risk is emitted.**

### Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ValidatedWeatherEvent",
  "type": "object",
  "required": [
    "event_id",
    "event_type",
    "validated",
    "affected_area",
    "source_stations"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "description": "Unique identifier of the validated atmospheric event."
    },
    "event_type": {
      "type": "string",
      "enum": ["extreme_heat", "heavy_rainfall", "flood_risk", "strong_wind", "storm_risk"],
      "description": "Meteorological category of the confirmed event."
    },
    "validated": {
      "type": "boolean",
      "enum": [true],
      "description": "Confirmation flag certifying the event has passed cross-station physical validation."
    },
    "affected_area": {
      "type": "string",
      "description": "Regional or municipal geographic area affected."
    },
    "source_stations": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "description": "List of station identifiers corroborating the event."
    }
  }
}
```

### Canonical Payload Example
```json
{
  "event_id": "E123",
  "event_type": "extreme_heat",
  "validated": true,
  "affected_area": "Delhi",
  "source_stations": [
    "AWS-104",
    "AWS-105",
    "AWS-108"
  ]
}
```

---

## 10. Disaster Risk Assessment Contract

### Source
* Emitted by Manan's Disaster Risk Model (integrated via Mitali's `risk_service.py`).
* Consumed by the Disaster Management Dashboard and the Public Safety Gateway.

### Ownership Boundary
* **Manan**: Owns risk-model development, risk-model training, and risk-model evaluation.
* **Mitali**: Owns risk-model integration, validation gate enforcement, context combination, event creation, database persistence, API exposure, and WebSocket broadcasting.
* The backend does **NOT** build a duplicate risk model.

### Initial & Future-Ready Event Types
* `extreme_heat`
* `heavy_rainfall`
* `flood_risk`
* `strong_wind`
* `storm_risk`

### Schema Specification
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DisasterRiskAssessment",
  "type": "object",
  "required": [
    "event_id",
    "event_type",
    "risk_level",
    "risk_score",
    "confidence",
    "validated",
    "affected_area",
    "evidence"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "description": "Reference identifier of the validated event."
    },
    "event_type": {
      "type": "string",
      "enum": ["extreme_heat", "heavy_rainfall", "flood_risk", "strong_wind", "storm_risk"],
      "description": "Classified disaster hazard type."
    },
    "risk_level": {
      "type": "string",
      "enum": ["low", "moderate", "high", "critical"],
      "description": "Operational threat level."
    },
    "risk_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Normalized risk severity score."
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Confidence score of the risk model prediction."
    },
    "validated": {
      "type": "boolean",
      "description": "Verification flag indicating whether the event has been reliability-certified."
    },
    "affected_area": {
      "type": "string",
      "description": "Geographical region assessed."
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Corroborating meteorological and spatial evidence statements."
    }
  }
}
```

### Canonical Payload Example
```json
{
  "event_id": "E123",
  "event_type": "extreme_heat",
  "risk_level": "high",
  "risk_score": 0.91,
  "confidence": 0.96,
  "validated": true,
  "affected_area": "Delhi",
  "evidence": [
    "Nearby stations agree",
    "Extreme temperature persisted",
    "Reading passed reliability checks"
  ]
}
```

---

## 11. Public / Citizen Safety Contract

### Source
* Served by Mitali's public safety gateway (`GET /api/public/risk/{area}`).
* Consumed by citizen mobile apps, web advisory banners, and municipal notification systems.

### Strict Privacy & Information Hiding Rules
The public safety endpoint **must NOT expose**:
* Sensor hardware IDs (e.g., `SNS-TMP-104`)
* Internal fault codes (e.g., `multivariate_inconsistency`)
* Raw model names or weights (e.g., `IsolationForest_v2`)
* Internal debug information or raw logs

### Official Advisory Rule
* **NEVER fabricate official advisories.**
* Never state "IMD issued an alert" or "NDMA declared an emergency" unless an authoritative, verified external official feed has been explicitly integrated.
* Use `"check_official_sources"` for `official_advisory_status`.

### Response Specification: Active Validated Risk
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PublicRiskResponse",
  "type": "object",
  "required": [
    "area",
    "risk_level",
    "event_type",
    "confidence",
    "message",
    "guidance",
    "official_advisory_status"
  ],
  "properties": {
    "area": {
      "type": "string",
      "description": "Geographic area for the advisory."
    },
    "risk_level": {
      "type": "string",
      "enum": ["low", "moderate", "high", "critical"],
      "description": "Public hazard level."
    },
    "event_type": {
      "type": "string",
      "description": "Public hazard category."
    },
    "confidence": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Confidence of the assessment."
    },
    "message": {
      "type": "string",
      "description": "Clear, non-technical explanatory message for the public."
    },
    "guidance": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Actionable, simple safety recommendations."
    },
    "official_advisory_status": {
      "type": "string",
      "enum": ["check_official_sources", "official_source_referenced"],
      "description": "Status instructing citizens to verify with official meteorological agencies."
    }
  }
}
```

#### Canonical Payload Example (Active Risk)
```json
{
  "area": "Delhi",
  "risk_level": "high",
  "event_type": "extreme_heat",
  "confidence": 0.96,
  "message": "High heat conditions detected and confirmed by multiple stations.",
  "guidance": [
    "Stay hydrated",
    "Avoid prolonged outdoor exposure"
  ],
  "official_advisory_status": "check_official_sources"
}
```

### Response Specification: No Validated Risk
When no genuine extreme event is active for an area (or when readings are uncertain or sensor faults):
```json
{
  "status": "no_validated_risk",
  "area": "Delhi"
}
```
* The system **never** manufactures an unvalidated warning.

---

## 12. Database Relational Entities Contract

### Entity Summary

| Entity | Primary Purpose | Key Contract Attributes |
| :--- | :--- | :--- |
| `stations` | Physical automated weather station metadata. | `station_id`, `station_name`, `area`, `latitude`, `longitude`, `elevation`, `status`, `created_at` |
| `sensors` | Individual sensor hardware on a station. | `sensor_id`, `station_id`, `sensor_type`, `installation_date`, `last_calibration_date`, `status` |
| `readings` | Raw, immutable time-series observations. | `reading_id`, `station_id`, `timestamp`, `temperature`, `pressure`, `humidity`, `wind_speed`, `wind_direction`, `rainfall`, `solar_radiation`, `latitude`, `longitude`, `area`, `elevation`, `source`, `quality_flag` |
| `anomalies` | Detected anomalies from ML adapter. | `anomaly_id`, `reading_id`, `anomaly`, `anomaly_score`, `model`, `signals_json`, `created_at` |
| `corrections` | Proposed non-destructive value adjustments. | `correction_id`, `reading_id`, `original_value`, `suggested_value`, `reason`, `confidence`, `review_status`, `reviewed_by`, `reviewed_at` |
| `sensor_health`| Digital Twin health profile and degradation metrics. | `health_id`, `sensor_id`, `health_score`, `drift_rate`, `failure_count`, `last_calibrated`, `updated_at` |
| `maintenance_queue`| Prioritized list of field interventions. | `queue_id`, `sensor_id`, `priority_rank`, `urgency_level`, `fault_reason`, `status`, `assigned_to` |
| `cascade_events`| Simulated downstream impact scenarios. | `cascade_id`, `reading_id`, `impact_domain`, `simulated_loss`, `severity`, `details_json` |
| `audit_log` | Comprehensive audit trail for system actions. | `log_id`, `actor`, `action`, `entity_type`, `entity_id`, `details`, `timestamp` |
| `risk_events` | Validated regional weather hazard episodes. | `event_id`, `station_id`, `event_type`, `start_time`, `end_time`, `affected_area`, `validation_status`, `source`, `created_at` |
| `risk_assessments` | Evaluated disaster risk scores and severity. | `risk_id`, `event_id`, `risk_level`, `risk_score`, `confidence`, `model_version`, `evidence`, `created_at` |

---

## 13. API Roadmap

### Core Reliability & Ingestion Endpoints
* `GET /api/stations` — List all monitored weather stations.
* `GET /api/stations/{id}` — Retrieve detailed station metadata.
* `GET /api/stations/{id}/readings` — Retrieve recent readings for a specific station.
* `GET /api/stations/{id}/health` — Retrieve Digital Twin hardware health profile.
* `POST /api/readings` — Ingest raw observation payload.
* `POST /api/inference` — Run full decision intelligence pipeline on a reading.
* `GET /api/anomalies` — List flagged anomalies.
* `GET /api/anomalies/{id}` — Retrieve specific anomaly details.
* `POST /api/corrections/{id}/accept` — Operator accepts non-destructive correction.
* `POST /api/corrections/{id}/reject` — Operator rejects suggested correction.
* `POST /api/corrections/{id}/review` — Operator submits manual value override with justification.
* `GET /api/maintenance` — Retrieve prioritized maintenance dispatch queue.
* `GET /api/cascade/{id}` — Retrieve downstream cascade impact simulation.

### Disaster Risk & Safety Endpoints (New)
* `GET /api/risks` — List all active disaster risk assessments (Disaster Management View).
* `GET /api/risks/{id}` — Retrieve detailed risk assessment with evidence breakdown.
* `GET /api/areas/{area}/risk` — Detailed regional risk evaluation for operational responders.
* `GET /api/public/risk/{area}` — Sanitized citizen-facing public safety advisory.

---

## 14. Real-Time WebSocket Roadmap (`/ws/live`)

### Transport
* WebSocket endpoint at `/ws/live` delivering typed JSON payloads to connected dashboards and alert channels.

### Event Payload Types
* `reading`: Emitted upon ingestion of an incoming sensor reading.
* `anomaly`: Emitted when Manan's ML adapter flags statistical rarity.
* `trust_update`: Emitted when Mitali's decision engine computes Trust Score and root cause.
* `digital_twin_update`: Emitted when sensor health or drift metrics update.
* `maintenance_update`: Emitted when maintenance priority queue re-ranks.
* `cascade_ready`: Emitted when cascade propagation simulation finishes.
* `risk_update`: Emitted when a validated genuine event yields a new Disaster Risk Assessment (Disaster Management View).
* `public_risk_update`: Emitted when sanitized public guidance changes for a region (Public / Citizen Safety View).
