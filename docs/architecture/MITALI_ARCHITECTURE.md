# SkyGuard AI — Mitali's Architecture Specification

## Module: Decision Intelligence, Backend Integration & Risk Integration

---

## 1. Executive Summary & Architectural Scope

In the SkyGuard AI system, **Mitali's module** provides the operational core, decision-making intelligence, backend infrastructure, and risk integration gateway. While initial anomaly detection identifies statistical outliers, Mitali's pipeline contextualizes these anomalies against physical laws, historical sensor behavior, and regional weather networks.

Following the validation of authentic weather phenomena, Mitali's module interfaces with downstream **Disaster Risk / Early Warning** and **Public / Citizen Safety** layers, ensuring emergency services and citizens receive reliable hazard assessments without exposing them to false alarms triggered by hardware sensor glitches.

---

## 2. End-to-End Pipeline Architecture

The end-to-end data, validation, decision, and risk flow operates sequentially as follows:

```text
WEATHER DATA
    ↓
ANOMALY MODEL
    ↓
CONSISTENCY ENGINE
    ↓
WEATHER vs SENSOR
    ↓
┌─────────────────────┐
│                     │
SENSOR FAULT       GENUINE WEATHER
│                     │
↓                     ↓
TRUST/FIX          EVENT VALIDATION
DIGITAL TWIN            ↓
MAINTENANCE          RISK MODEL
                         ↓
                ┌────────┴────────┐
                ↓                 ↓
          DISASTER VIEW     CITIZEN VIEW
```

---

## 3. Critical Safety & Architectural Invariants

### 3.1. The Fundamental Safety Rule
> **NEVER IMPLEMENT:**
>
> `extreme reading` $\longrightarrow$ `disaster alert`

Automated weather sensors deployed in harsh environmental conditions suffer frequent hardware faults (e.g., thermal spikes, electrical shorts, stuck sensors, calibration drifts). Directly wiring an extreme observation to an emergency hazard notification triggers catastrophic false alarms, eroding public trust and exhausting emergency response resources.

### 3.2. The Multi-Tier Verification Gate
The required operational flow is strictly guarded by reliability evidence:

```text
extreme reading
    ↓
anomaly detection
    ↓
temporal consistency
    ↓
cross-sensor consistency
    ↓
cross-station consistency
    ↓
weather-vs-sensor decision
    ↓
genuine weather?
    ↓ YES
validated event
    ↓
risk assessment
```

### 3.3. Failure & Uncertainty Gating Rules
1. **`sensor_fault` BLOCKS disaster risk**:
   If the decision engine determines that an anomaly is caused by hardware failure, **NO disaster event is created**. The reading is routed exclusively to Trust Score downgrading, fault classification, value correction, Digital Twin degradation tracking, and field maintenance queuing.
2. **`uncertain` BLOCKS automatic public risk**:
   If spatial or temporal evidence is inconclusive, conflicting, or sparse, the decision is marked `uncertain`. The system **NEVER** issues an automated public hazard alert. The event is held for operator inspection.
3. **Sufficient Corroboration Required**:
   Disaster risk outputs and citizen advisories require positive verification from multiple corroborating evidence dimensions (spatial neighbor agreement, thermodynamic multi-sensor consistency, and physical persistence).

---

## 4. Team Ownership & Operational Boundaries

To maintain software engineering integrity across the six-member team, responsibilities are strictly partitioned:

| Member | Sub-Team Domain | Concrete Ownership | Operational Boundary |
| :--- | :--- | :--- | :--- |
| **Manan** | ML + EDA | **Anomaly Detection & Risk Modeling** | Develops, trains, and evaluates Statistical, Isolation Forest, Autoencoder, Hybrid anomaly models, and ML Disaster Risk models. |
| **Muskan** | ML + Data Collection | **Dataset Engineering & Fault Injection** | Generates synthetic hardware fault archetypes (`temperature_spike`, `drift`, `frozen_sensor`, `dropout`, `jump`, `bias`, `noise`, `multivariate_inconsistency`), benchmark splits, and experiment registry. |
| **Neha** | Data Collection + EDA | **Real Weather Data Pipeline & Quality** | Ingests real weather telemetry, audits missingness/duplicates, validates timestamps, provides geographical/station metadata, and conducts data quality EDA. |
| **Mitali** | ML + Backend | **Decision Intelligence, Backend & Risk Integration** | Integrates ML anomaly and risk models via decoupled adapters; builds temporal, cross-sensor, and cross-station consistency engines; implements weather-vs-sensor decision, Trust Score, explanations, corrections, Digital Twin, maintenance queues, APIs, database, WebSockets, replay, cascade, and public safety transformations. |
| **Medhvi** | Frontend + EDA | **Visual Analytics & Information Architecture** | Designs dashboard layouts, time-series charts, spatial station networks, Trust Score displays, Digital Twin profiles, maintenance dispatch interfaces, and dual-view hazard screens (Disaster View & Citizen View). |
| **Darshita** | Frontend | **React Frontend Implementation** | Implements the interactive React web application based on Medhvi's designs, integrating with Mitali's REST APIs and `/ws/live` streaming WebSocket feeds. |

### Explicit ML Ownership Boundary:
* **Manan** owns model development, training, feature weights, and evaluation metrics for anomaly detection and risk scoring.
* **Mitali** does **NOT** train or build duplicate ML/risk models inside the backend. Mitali integrates Manan's model outputs behind clean adapter abstractions, applies the validation gates, manages state, and exposes operational services.

---

## 5. Layer-by-Layer Architectural Breakdown

### 5.1. Ingestion Layer (`backend/app/api/` & `backend/app/schemas/`)
* Ingests automated weather station observations via REST endpoints and real-time streaming interfaces.
* Validates schema integrity (using Pydantic models conforming to the 16-variable canonical contract), normalizes timestamps to UTC ISO 8601, and enriches station metadata.

### 5.2. ML Anomaly Adapter (`ml/integration/`)
* Decouples the backend from ML library internals (scikit-learn, PyTorch, TensorFlow).
* Exposes a stable interface: `result = inference_service.predict(reading, context)`.
* Transforms backend reading payloads into model feature matrices and normalizes outputs into the unified `AnomalyResult` contract (`anomaly`, `anomaly_score`, `model`, `signals`).

### 5.3. Consistency & Evidence Collection Layer (`backend/app/services/`)
When an observation is flagged as statistically unusual, the consistency engine gathers evidence across three orthogonal dimensions of physical reality:
1. **Temporal Evidence**:
   * Analyzes rate of change ($dx/dt$), persistence across observation epochs, and diurnal curve compliance.
2. **Cross-Sensor Evidence**:
   * Evaluates thermodynamic correlations across co-located sensors (e.g., verifying if a temperature surge corresponds with an expected drop in relative humidity and barometric shift).
3. **Cross-Station Evidence**:
   * Assesses spatial coherence against neighboring stations within a geographic radius using `station_neighbors.csv` (inverse-distance weighted consensus).

### 5.4. Reasoning & Decision Engine (`reasoning_service.py`)
* Synthesizes multidimensional evidence vectors to categorize the root cause into exactly one of three definitive states:
  * `genuine_weather`
  * `sensor_fault`
  * `uncertain`
* Enforces the rule that conflicting or insufficient evidence yields `uncertain`, never an arbitrary binary guess.

### 5.5. Operational Hardware Tracks (`sensor_fault`)
When an anomaly is attributed to a sensor failure:
* **Trust Scoring Engine (`trust_service.py`)**: Computes an actionable `0–100` reliability metric. (Note: `anomaly_score != trust_score`).
* **Fault Classifier (`fault_classifier.py`)**: Classifies the failure signature into operational archetypes (`temperature_spike`, `drift`, `frozen_sensor`, `dropout`, `abrupt_jump`, `bias`, `noise`, `multivariate_inconsistency`).
* **Explanation Engine (`explanation_service.py`)**: Generates human-interpretable reasoning points detailing why the reading failed physical checks.
* **Correction Suggestion Engine (`correction_service.py`)**: Calculates non-destructive imputed candidate values for human review without modifying raw records.
* **Digital Twin & Sensor Health (`digital_twin_service.py`)**: Tracks hardware degradation, drift accumulation, and fault frequency over time.
* **Maintenance Queue Prioritization (`maintenance_service.py`)**: Orders field technician dispatch based on station criticality, error severity, and network impact.
* **Cascade Simulator (`cascade_service.py`)**: Models downstream ripple effects on external systems (hydrology, agriculture, aviation).

### 5.6. Validated Weather Event Extractor & Safety Gate
* When the decision engine outputs `genuine_weather`, the observation is extracted into a `ValidatedWeatherEvent`.
* The event record aggregates reporting stations, confirms physical validity, and establishes geographic boundaries.
* **Unvalidated readings, sensor faults, and uncertain observations are strictly prohibited from entering this stage.**

### 5.7. Disaster Risk Integration Layer (`risk_service.py`)
* Consumes validated weather events and invokes Manan's ML Disaster Risk Model adapter.
* Evaluates hazard categories:
  * `extreme_heat`
  * `heavy_rainfall`
  * `flood_risk`
  * `strong_wind`
  * `storm_risk`
* Produces a structured `DisasterRiskAssessment` containing `risk_level` (`low`, `moderate`, `high`, `critical`), `risk_score` (0.0 to 1.0), `confidence`, and supporting meteorological evidence.

### 5.8. Dual-View Delivery Gateways

SkyGuard AI routes risk intelligence through two distinct operational views tailored to their audiences:

```text
               DisasterRiskAssessment
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
[Disaster Management View]     [Public / Citizen Safety View]
  - Full technical metrics       - Non-technical explanations
  - Sensor hardware IDs          - Actionable safety guidance
  - Raw evidence vectors         - "check_official_sources"
  - Inter-station correlations   - Strict privacy & info hiding
  - Dispatch & operations        - No internal IDs or models
```

1. **Disaster Management View (`/api/risks`, `/api/areas/{area}/risk`)**:
   * Dedicated to emergency operations centers, municipal responders, and meteorologists.
   * Exposes full diagnostic depth: participating station IDs, sub-sensor readings, confidence intervals, spatial consistency scores, and raw evidence bullets.
2. **Public / Citizen Safety View (`/api/public/risk/{area}`)**:
   * Dedicated to public dashboards, civic mobile applications, and citizen alerts.
   * **Information Hiding**: Completely strips sensor hardware IDs, fault codes, raw ML model designations, and internal debug data.
   * **Clear Guidance**: Delivers actionable advice (e.g., "Stay hydrated", "Avoid prolonged outdoor exposure").
   * **Official Advisory Integrity**: Never fabricates statements from government agencies (e.g., IMD, NDMA). Uses `"check_official_sources"` status.
   * **No Validated Risk Output**: When no validated risk exists, cleanly returns `{"status": "no_validated_risk", "area": "..."}` without generating alarm.

---

## 6. The Core Three-Tier Architectural Distinction

To avoid architectural confusion, SkyGuard separates its three analysis stages:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. ANOMALY DETECTION (Manan)                                │
│    "Is this observation statistically atypical?"            │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. DECISION INTELLIGENCE (Mitali)                           │
│    "Is this atypical observation real weather or a fault?"  │
│    "Can downstream systems trust this observation?"         │
└─────────────────────────────┬───────────────────────────────┘
                              ▼ (Only if genuine_weather)
┌─────────────────────────────────────────────────────────────┐
│ 3. DISASTER RISK ASSESSMENT (Manan Model + Mitali Gate)     │
│    "Given this validated event, what is the hazard risk     │
│     and what action should citizens and responders take?"   │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Database Entities (Relational Persistence)

The relational schema stores all system states with complete auditability and non-destructive immutability:

| Entity Name | Primary Purpose | Planned Attributes |
| :--- | :--- | :--- |
| `stations` | Physical automated weather station metadata. | `id`, `station_code`, `name`, `latitude`, `longitude`, `elevation`, `status`, `created_at` |
| `sensors` | Individual sensor hardware units mounted on stations. | `id`, `station_id`, `sensor_type`, `model`, `install_date`, `calibration_date`, `status` |
| `readings` | Raw, immutable time-series observations. | `id`, `station_id`, `timestamp`, `temperature`, `pressure`, `humidity`, `wind_speed`, `wind_direction`, `rainfall`, `solar_radiation`, `latitude`, `longitude`, `area`, `elevation`, `source`, `quality_flag` |
| `anomalies` | Flagged statistical anomalies from ML adapter. | `id`, `reading_id`, `is_anomaly`, `anomaly_score`, `model_source`, `signals_json`, `created_at` |
| `corrections` | Proposed non-destructive value adjustments. | `id`, `reading_id`, `original_value`, `suggested_value`, `reason`, `confidence`, `status`, `reviewed_by`, `reviewed_at` |
| `sensor_health` | Digital Twin degradation profiles. | `id`, `sensor_id`, `health_score`, `drift_rate`, `failure_count`, `last_calibrated`, `updated_at` |
| `maintenance_queue`| Prioritized field intervention dispatch list. | `id`, `sensor_id`, `priority_rank`, `urgency_level`, `fault_reason`, `status`, `assigned_to` |
| `cascade_events` | Simulated downstream impact models. | `id`, `reading_id`, `impact_domain`, `simulated_loss`, `severity`, `details_json` |
| `audit_log` | Immutable audit log of all human and automated actions.| `id`, `actor`, `action`, `entity_type`, `entity_id`, `details`, `timestamp` |
| `risk_events` | Validated regional weather hazard episodes. | `id`, `event_id`, `station_id`, `event_type`, `start_time`, `end_time`, `affected_area`, `validation_status`, `source`, `created_at` |
| `risk_assessments`| Evaluated disaster risk scores and severity. | `id`, `risk_id`, `event_id`, `risk_level`, `risk_score`, `confidence`, `model_version`, `evidence_json`, `created_at` |

---

## 8. Service Architecture Decomposition (`backend/app/services/`)

Backend services are strictly decoupled into single-responsibility modules:

1. `inference_service.py`: Orchestrates ingestion, calls ML anomaly adapter, coordinates consistency checks, and produces evaluation results.
2. `reasoning_service.py`: Evaluates temporal, cross-sensor, and cross-station evidence to determine `genuine_weather`, `sensor_fault`, or `uncertain`.
3. `trust_service.py`: Calculates the calibrated `0–100` operational Trust Score.
4. `fault_classifier.py`: Categorizes sensor failure modes into operational archetypes.
5. `explanation_service.py`: Generates transparent bullet points detailing evidence sources.
6. `correction_service.py`: Manages non-destructive value imputation and human review lifecycles.
7. `digital_twin_service.py`: Maintains hardware degradation tracking and drift modeling.
8. `maintenance_service.py`: Orders the field dispatch queue based on urgency and impact.
9. `cascade_service.py`: Simulates downstream impact across agricultural, hydrological, and aviation sectors.
10. `risk_service.py`: Enforces the validation gate, integrates Manan's ML Disaster Risk Model, and manages risk assessments for the Disaster Management View.
11. `public_safety_service.py`: Transforms validated risk assessments into sanitized, citizen-facing public safety advisories.

*(Note: In accordance with Phase 0 constraints and contract-reconciliation boundaries, service modules are documented for architectural readiness and implemented progressively in their designated phases.)*
