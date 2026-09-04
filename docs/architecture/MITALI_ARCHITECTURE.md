# SkyGuard AI — Mitali's Architecture Specification

## Module: Decision Intelligence & Backend Integration

---

## 1. Executive Summary & Architectural Scope

In the SkyGuard AI system, **Mitali's module** provides the operational core and decision-making intelligence. While initial anomaly detection identifies statistical outliers, Mitali's pipeline contextualizes these anomalies against physical laws, historical sensor behavior, and regional weather networks.

This document formalizes the architectural blueprint, data flows, core algorithmic layers, operational states, and design principles governing Mitali's subsystem across future implementation phases.

---

## 2. End-to-End Pipeline Architecture

The end-to-end data and reasoning flow for incoming sensor readings proceeds sequentially through well-defined layers:

```text
                    WEATHER READING
                           │
                           ▼
                    FastAPI Backend
                           │
                           ▼
                 ML Anomaly Adapter
                           │
                           ▼
                    Anomaly Result
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Temporal         Cross-Sensor    Cross-Station
       Evidence          Evidence         Evidence
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                       Persistence
                           │
                           ▼
                     Decision Engine
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       Genuine Weather Sensor Fault  Uncertain
                           │
                           ▼
                       Trust Score
                           │
                           ▼
                    Fault Classifier
                           │
                           ▼
                      Explanation
                           │
                           ▼
                  Correction Suggestion
                           │
                           ▼
                     Digital Twin
                           │
                           ▼
                  Maintenance Queue
                           │
                           ▼
                  Cascade Simulator
```

---

## 3. Layer-by-Layer Architectural Breakdown

### 3.1. Ingestion Layer (`backend/app/api/` & `backend/app/schemas/`)
* **Role**: Ingests automated weather station observations via REST endpoints and real-time streaming interfaces.
* **Responsibilities**: Schema validation (via Pydantic), timestamp normalization (UTC ISO 8601), metadata enrichment, and dispatching to internal processing pipelines.

### 3.2. ML Anomaly Adapter (`ml/integration/`)
* **Role**: Architectural decoupling boundary between the backend and ML anomaly detection models.
* **Responsibilities**:
  * Transforms raw backend reading schemas into the feature vectors expected by anomaly models.
  * Consumes model inference outputs and standardizes them into the unified `AnomalyResult` contract.
  * Shields backend services from underlying model choices (Isolation Forest, Autoencoders, statistical methods, or future deep learning models).

### 3.3. Evidence Collection Layer (`backend/app/services/`)
When an anomaly is flagged, the evidence collection engine evaluates three orthogonal dimensions of physical reality:
1. **Temporal Evidence (`temporal_service.py` / `reasoning_service.py`)**:
   * Evaluates the rate of change ($dx/dt$), persistence over consecutive observation windows, and historical diurnal variance for the specific sensor.
2. **Cross-Sensor Evidence (`cross_sensor_service.py` / `reasoning_service.py`)**:
   * Validates inter-variable thermodynamic consistency on the same physical station (e.g., verifying if a temperature rise corresponds with expected relative humidity drops, or if barometric pressure drops align with sudden gusting).
3. **Cross-Station Evidence (`cross_station_service.py` / `reasoning_service.py`)**:
   * Assesses spatial correlation with neighboring weather stations within a defined geospatial radius (e.g., inverse-distance weighted consensus).

### 3.4. Persistence Layer (`backend/app/database/` & `backend/app/models/`)
* **Role**: ACID-compliant relational persistence tracking readings, decisions, audit logs, and hardware lifecycles.
* **Principle**: Raw data integrity is immutable. Derived inferences, corrections, and audit events are stored in dedicated relational tables with strict foreign-key relationships.

### 3.5. Reasoning & Decision Engine (`reasoning_service.py`)
* **Role**: Synthesizes multidimensional evidence vectors to categorize the root cause into one of three definitive states: `genuine_weather`, `sensor_fault`, or `uncertain`.

### 3.6. Trust Scoring Engine (`trust_service.py`)
* **Role**: Computes an actionable `0–100` reliability score indicating downstream operational trustworthiness.

### 3.7. Fault Classifier (`fault_classifier.py`)
* **Role**: If a reading is determined to be a `sensor_fault`, classifies the failure signature into specific operational failure modes (e.g., `temperature_spike`, `drift`, `frozen_sensor`, `dropout`, `bias`).

### 3.8. Explanation Engine (`explanation_service.py`)
* **Role**: Produces structured, human-readable explanations detailing which evidence sources supported or refuted the reading, enabling operators to understand automated decisions instantly.

### 3.9. Correction Suggestion Engine (`correction_service.py`)
* **Role**: Generates non-destructive, physically consistent imputed values based on neighboring station consensus and temporal trend interpolation.

### 3.10. Digital Twin & Sensor Health Service (`digital_twin_service.py`)
* **Role**: Maintains persistent health profiles for every physical hardware sensor, tracking cumulative drift, fault frequency, noise floors, and degradation over time.

### 3.11. Maintenance Queue Prioritization (`maintenance_service.py`)
* **Role**: Converts sensor health degradation into an operational priority queue for field technicians, calculating priority based on station criticality, fault severity, and data impact.

### 3.12. Cascade Simulator (`simulator/cascade/` & `cascade_service.py`)
* **Role**: Simulates how erroneous or uncorrected sensor data would propagate downstream into hydrological forecasts, fire weather indices, agricultural advisory models, or aviation warnings.

---

## 4. The Core Architectural Distinction: Anomaly Detection vs. Decision Intelligence

A foundational requirement of SkyGuard AI is maintaining the clear architectural boundary between **Manan's module** and **Mitali's module**:

```text
┌─────────────────────────────────────────────────────────────┐
│                       MANAN'S DOMAIN                        │
│                                                             │
│                    WEATHER READING                          │
│                           │                                 │
│                           ▼                                 │
│                   Anomaly Detection                         │
│                           │                                 │
│                           ▼                                 │
│               "Something looks unusual."                    │
└─────────────────────────────┬───────────────────────────────┘
                              │ Standardized Contract
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      MITALI'S DOMAIN                        │
│                                                             │
│                        Anomaly                              │
│                           +                                 │
│                   Temporal Evidence                         │
│                           +                                 │
│                 Cross-Sensor Evidence                       │
│                           +                                 │
│                Cross-Station Evidence                       │
│                           +                                 │
│                  Persistence History                        │
│                           +                                 │
│                 Historical Sensor Health                    │
│                           │                                 │
│                           ▼                                 │
│              "What does this anomaly mean?"                 │
└─────────────────────────────────────────────────────────────┘
```

* **Manan's Models Answer**: *"Is this observation statistically atypical relative to baseline distributions?"*
* **Mitali's Engine Answers**: *"Does this atypical observation reflect a real atmospheric phenomenon or hardware failure, why did it occur, can we trust it, what is the corrected value, and does the sensor need replacement?"*

---

## 5. Future Decision States

The decision engine evaluates evidence and outputs exactly one of three valid states:

### 1. `genuine_weather`
* **Definition**: The anomaly is confirmed to be an authentic atmospheric event.
* **Criteria**: Nearby stations exhibit congruent shifts, cross-variable physical relationships remain thermodynamically valid, and regional pressure/wind indicators corroborate localized atmospheric turbulence.
* **Downstream Action**: Data is certified authentic; downstream consumers are alerted to significant meteorological conditions.

### 2. `sensor_fault`
* **Definition**: The anomaly is attributed to mechanical, electrical, or software failure of the physical sensor.
* **Criteria**: Severe divergence from all neighboring stations, impossible rate of change exceeding physical limits, violation of multi-variable correlations (e.g., 50°C temperature with 99% RH and steady high pressure), or chronic sensor degradation patterns.
* **Downstream Action**: Trust score downgraded, fault classified, non-destructive correction suggested, maintenance score updated.

### 3. `uncertain`
* **Definition**: The evidence is inconclusive, conflicting, or insufficient to reach a high-confidence determination.
* **Criteria**: Sparse station network coverage, conflicting neighboring trends, intermittent communication dropouts, or borderline evidence scores.
* **Core Rule**: **Never force the system to pick between genuine weather and sensor fault when evidence is insufficient.** Forcing binary classification under uncertainty leads to catastrophic false alarms or dangerous blind spots. The system explicitly flags `uncertain` for human operator inspection.

---

## 6. The Trust Score Concept (0–100)

The **Trust Score** is an operational metric ranging from `0` to `100`. 

> **Critical Architectural Principle**: The **Trust Score is NOT the inverse of the Anomaly Score.**

* **Anomaly Score ($0.0 \to 1.0$)**: Quantifies *statistical rarity*. An extreme tropical cyclone or tornadic pressure drop will produce a very high Anomaly Score ($>0.95$).
* **Trust Score ($0 \to 100$)**: Quantifies *operational dependability*. 

### Illustrative Scenarios:

| Metric | Scenario A: Extreme Storm Front | Scenario B: Defective Temperature Probe |
| :--- | :--- | :--- |
| **Observation** | Temperature drops 12°C in 15 mins; Barometer plunges 8 hPa. | Temperature spikes from 22°C to 58°C in 1 minute. |
| **Anomaly Score** | **0.96** *(Extremely unusual event)* | **0.96** *(Extremely unusual event)* |
| **Evidence** | Confirmed by 4 neighboring stations; humidity surged to 95%; wind gusted to 60 kt. | 0 neighboring stations show heat; humidity unchanged; pressure flat. |
| **Decision** | `genuine_weather` | `sensor_fault` |
| **Trust Score** | **91 / 100** *(Highly trustworthy real-world reading)* | **18 / 100** *(Untrustworthy corrupted reading)* |

Downstream automated systems (e.g., flood gates, agricultural irrigation controllers, flight planning systems) rely on the **Trust Score**, not the raw Anomaly Score.

---

## 7. The Correction & Non-Destructive Ingestion Principle

SkyGuard AI enforces strict data governance and auditability:

```text
[Raw Reading: 55.0°C] ───(Persisted Immutably)───► `readings` table
           │
           ├───► Evaluated by Decision Engine ───► `sensor_fault`
           │
           └───► Imputation Engine ───► [Suggested Correction: 31.8°C]
                                                    │
                                                    ▼
                                            `corrections` table
                                       (Status: PENDING_REVIEW)
                                                    │
                                      ┌─────────────┴─────────────┐
                                      ▼                           ▼
                                  [ACCEPTED]                  [REJECTED]
```

1. **Immutability of Primary Data**: Raw sensor telemetry is NEVER overwritten, modified, or deleted in place.
2. **Dual-Store Architecture**: Suggested corrections exist as separate relational records linked via foreign keys to the original raw reading.
3. **Review Lifecycle**: Every correction follows a strict lifecycle: `SUGGESTED` $\to$ `PENDING_REVIEW` $\to$ `ACCEPTED` / `REJECTED`.
4. **Audit Trail**: Every automated adjustment, human acceptance, or rejection is logged with user attribution and timestamp in the `audit_log`.

---

## 8. Planned Database Entities (Relational Schema Overview)

| Entity Name | Primary Purpose | Planned Attributes |
| :--- | :--- | :--- |
| `stations` | Physical automated weather station metadata. | `id`, `station_code`, `name`, `latitude`, `longitude`, `elevation`, `status`, `created_at` |
| `sensors` | Individual sensor hardware on a station. | `id`, `station_id`, `sensor_type`, `model`, `install_date`, `calibration_date`, `status` |
| `readings` | Raw, immutable time-series observations. | `id`, `sensor_id`, `timestamp`, `temperature`, `pressure`, `humidity`, `raw_payload`, `quality_flag` |
| `anomalies` | Detected anomalies from ML adapter. | `id`, `reading_id`, `is_anomaly`, `anomaly_score`, `model_source`, `signals_json`, `created_at` |
| `corrections` | Proposed non-destructive value adjustments. | `id`, `reading_id`, `original_value`, `suggested_value`, `status`, `reviewed_by`, `reviewed_at` |
| `sensor_health` | Digital Twin health profile and degradation metrics. | `id`, `sensor_id`, `health_score`, `drift_rate`, `failure_count`, `last_calibrated`, `updated_at` |
| `maintenance_queue`| Prioritized list of required field interventions. | `id`, `sensor_id`, `priority_rank`, `urgency_level`, `fault_reason`, `status`, `assigned_to` |
| `cascade_events` | Simulated downstream impact scenarios. | `id`, `reading_id`, `impact_domain`, `simulated_loss`, `severity`, `details_json` |
| `audit_log` | Comprehensive audit trail for system actions. | `id`, `actor`, `action`, `entity_type`, `entity_id`, `details`, `timestamp` |

---

## 9. Future Service Architecture (`backend/app/services/`)

To guarantee maintainability, high cohesion, and loose coupling, backend intelligence is decomposed into isolated single-responsibility service modules:

1. `inference_service.py`: Orchestrates ingestion, calls the ML adapter, gathers evidence, and coordinates the evaluation pipeline.
2. `reasoning_service.py`: Implements temporal, cross-sensor, and cross-station evidence synthesis to determine `genuine_weather`, `sensor_fault`, or `uncertain`.
3. `trust_service.py`: Evaluates evidence weights and calculates the final `0–100` Trust Score.
4. `fault_classifier.py`: Categorizes sensor faults into failure archetypes (`temperature_spike`, `drift`, `frozen_sensor`, etc.).
5. `explanation_service.py`: Assembles plain-language explanatory bullet points for analysts and operators.
6. `correction_service.py`: Calculates non-destructive imputed candidate values and handles the review lifecycle.
7. `digital_twin_service.py`: Maintains long-term sensor health tracking, drift modeling, and degradation metrics.
8. `maintenance_service.py`: Computes urgency metrics and orders the field maintenance dispatch queue.
9. `cascade_service.py`: Models and simulates the downstream ripple effects of erroneous sensor inputs.

*(Note: In accordance with Phase 0 constraints, these service modules are documented for architectural readiness and will be implemented progressively in subsequent phases.)*
