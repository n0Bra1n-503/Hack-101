# SkyGuard AI

> AI-powered weather sensor reliability, decision-intelligence, and disaster early-warning system.

---

## 1. Problem Statement

Weather stations and Automated Weather Systems (AWS) frequently produce anomalous sensor readings. When an unusual reading occurs (e.g., an abrupt temperature surge or sudden pressure drop), it typically stems from one of two fundamentally different realities:

1. **A Genuine Atmospheric Event**: Microbursts, storm fronts, sudden precipitation cooling, localized convective activity, or chinook/foehn wind effects.
2. **A Sensor Malfunction**: Hardware degradation, electrical noise, calibration drift, bio-fouling, frozen sensors, dropout, or multivariate inconsistency.

A simple anomaly detector alone cannot reliably distinguish between these two phenomena. It merely flags statistical deviations without understanding physical context or cross-station coherence. 

**SkyGuard AI** bridges this critical gap by fusing initial anomaly detection with multi-dimensional evidence—evaluating temporal stability, cross-sensor physical correlation, and cross-station spatial consistency—to determine whether an abnormal reading is an atmospheric anomaly or hardware failure.

**Critical Safety Guardrail**: Extreme readings must **NEVER** directly trigger disaster alerts. Only readings verified and validated as authentic `genuine_weather` advance to disaster risk assessment and public safety guidance. Sensor faults strictly block disaster alerts.

---

## 2. Core Question

> **"Is this unusual reading actually trustworthy?"**

---

## 3. Core System Outputs

For any monitored weather reading, SkyGuard AI produces:

* **Anomaly Detection**: Whether an observation deviates statistically or structurally from nominal patterns.
* **Weather vs Sensor Decision**: Clear categorization into `genuine_weather`, `sensor_fault`, or `uncertain`.
* **Trust Score**: A calibrated reliability metric ranging from `0` to `100` representing downstream dependability.
* **Confidence**: Statistical confidence in the classification decision.
* **Fault Type**: Specific classification of sensor failure (e.g., `temperature_spike`, `drift`, `frozen_sensor`).
* **Explanation**: Transparent, human-interpretable rationale detailing supporting and contradicting evidence.
* **Suggested Correction**: An imputed, physically consistent estimate proposed for operator review without modifying raw records.
* **Sensor Health / Digital Twin**: Long-term degradation tracking and health profiling for individual physical sensors.
* **Maintenance Priority**: Operational ranking identifying which field units urgently require calibration or physical service.
* **Cascade Impact**: Predictive simulation showing how corrupt or uncalibrated readings propagate downstream to forecasting and agricultural models.
* **Validated Weather Event**: Verified genuine atmospheric episodes corroborated across neighboring stations.
* **Disaster Risk Assessment**: Quantitative threat severity evaluation (`extreme_heat`, `heavy_rainfall`, `flood_risk`, etc.) for emergency managers.
* **Public / Citizen Safety View**: Sanitized, non-technical advisories and actionable guidance with official agency safety checks.

---

## 4. High-Level Architecture Pipeline

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

## 5. Team Ownership & Responsibilities

The SkyGuard AI project architecture is split across six specialized team members:

| Member | Domain | Specific Responsibility | Key Deliverables / Focus Areas |
| :--- | :--- | :--- | :--- |
| **Manan** | ML + EDA | **Anomaly Detection & Risk Modeling** | Statistical anomaly detection, Isolation Forest, Autoencoders, hybrid anomaly models, feature engineering, ML-oriented EDA, anomaly evaluation, and ML disaster risk models. |
| **Muskan** | ML + Data Collection | **ML Dataset Engineering + Fault Injection** | Synthetic fault injection (`temperature_spike`, `drift`, `frozen_sensor`, `dropout`, `jump`, `bias`, `noise`, `multivariate_inconsistency`), benchmark datasets, clean splits, and experiment registry. |
| **Neha** | Data Collection + EDA | **Real Weather Data Pipeline + Data Quality** | Real weather data discovery, station selection, raw ingestion, metadata, missingness/duplicate auditing, timestamp validation, basic validity checks, and data quality EDA. |
| **Mitali** | ML + Backend | **Decision Intelligence, Backend & Risk Integration** | Integrates anomaly and risk models via decoupled adapters, develops evidence gathering (temporal, cross-sensor, cross-station), persistence, weather-vs-sensor decision engine, trust scoring, fault classification, explanations, corrections, digital twin, maintenance prioritization, APIs, cascade simulation, and public safety transformations. |
| **Medhvi** | Frontend + EDA | **Visual Analytics + Information Architecture** | Dashboard UX structure, visual analytics, time-series charts, spatial station comparisons, Trust Score visualization, Digital Twin health profiles, maintenance queues, cascade visualization design, and dual-view hazard screens (Disaster View & Citizen View). |
| **Darshita** | Frontend | **React Frontend Implementation + UX Interaction** | Implements the interactive React web application based on Medhvi's information architecture and designs, integrating with the backend APIs and real-time streaming sockets. |

---

## 6. Mitali's Module Responsibility

Mitali's module centers on **Decision Intelligence, Backend Integration, and Risk Integration**.

### Important Boundary:
Mitali does **NOT** own or train Manan's anomaly detection or risk models. Manan's models answer:
> *"Does this reading look unusual?"* and *"Given a validated event, what is the risk score?"*

Mitali's pipeline contextualizes anomalies, validates authenticity, and manages operational decisions:
> *"What does this anomaly actually mean, can it be trusted, why or why not, is it a confirmed hazard, and what operational action should be taken?"*

Mitali's subsystem encapsulates:
* **ML Anomaly & Risk Adapters**: Decoupled integration layers consuming model predictions from Manan without binding backend logic to specific ML frameworks.
* **Evidence Gathering**: Multi-source corroboration combining temporal history, physical multi-variable correlation (e.g., temperature vs. humidity vs. pressure), and spatial neighbors.
* **Reasoning & Trust Engine**: Producing a tri-state decision (`genuine_weather`, `sensor_fault`, `uncertain`) and a calibrated 0–100 Trust Score.
* **Operational Engines**: Fault classification, explanatory reporting, non-destructive value correction, sensor digital twins, maintenance queue prioritization, and cascade simulation.
* **Validated Weather Event Extraction**: Safety gate ensuring only confirmed genuine events enter risk assessment.
* **Backend API & Real-Time Ingestion**: FastAPI services, relational persistence, and WebSocket real-time delivery (`/ws/live`).
* **Public Safety Transformation**: Transforming technical risk models into sanitized, citizen-safe guidance while shielding internal hardware IDs and fault diagnostics.

---

## 7. Implementation Roadmap & Development Status

| Phase | Milestone Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | Architecture, Data Contracts & Reconciliation | **COMPLETED** |
| **Phase 1** | Backend Foundation + Weather Data Ingestion | **COMPLETED (CURRENT)** |
| **Phase 2** | Synthetic Fault Injection & Benchmark Dataset | *UPCOMING* |
| **Phase 3** | Feature Engineering & Anomaly Detection Pipeline | *UPCOMING* |
| **Phase 4** | Consistency Engine & Decision Intelligence (Weather vs Sensor) | *UPCOMING* |
| **Phase 5** | Trust Scoring, Explanations & Value Corrections | *UPCOMING* |
| **Phase 6** | Digital Twin, Sensor Health & Maintenance Prioritization | *UPCOMING* |
| **Phase 7** | Validated Weather Events & Disaster Risk Integration | *UPCOMING* |
| **Phase 8** | Public / Citizen Safety View & API Gateway | *UPCOMING* |
| **Phase 9** | Real-Time WebSocket Streaming (`/ws/live`) | *UPCOMING* |
| **Phase 10** | Downstream Cascade Impact Simulator | *UPCOMING* |
| **Phase 11** | Frontend Integration (Darshita & Medhvi) | *UPCOMING* |

### Phase 1 Deliverables:
* **FastAPI Application**: Operational backend serving `GET /`, `GET /health`, and auto-docs at `/docs`.
* **Telemetry Ingestion**: `POST /api/readings` validating 16-variable canonical weather observations with Pydantic.
* **Extreme Weather Acceptance**: Accepts extreme observations (e.g., 55°C) without domain bias; authenticity determination deferred to ML phases.
* **Persistent Storage**: SQLAlchemy ORM storing immutable raw observations in SQLite/PostgreSQL with composite indexes.
* **Retrieval APIs**: `GET /api/stations/{id}/readings` with time-range filtering and `GET /api/readings/{id}`.
* **Automated Tests**: Complete test coverage via `pytest` (`tests/test_ingestion.py`).
