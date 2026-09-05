# SkyGuard AI — Full Production Integration & Architecture Manual

This manual provides the forensic, end-to-end documentation for the SkyGuard AI weather sensor reliability, decision intelligence, and disaster management platform.

---

## 1. Pipeline Architecture

SkyGuard AI enforces a strictly unidirectional, decoupled pipeline architecture:

```
REAL WEATHER OBSERVATIONS (AWS Gujarat & Maharashtra Telemetry)
                           ↓
STREAMING VALIDATION & NORMALIZATION (NaN → NULL, Deterministic SHA-256 IDs, Bhadar Dam Disambiguation)
                           ↓
SUPABASE POSTGRESQL (readings, stations, anomalies, corrections, sensor_health, risk_events)
                           ↓
MANAN PRE-TRAINED ML ANOMALY DETECTORS (Isolation Forest, Tabular Autoencoder, Statistical Baseline)
                           ↓
HYBRID ANOMALY SIGNAL FUSION ({ anomaly: bool, anomaly_score: float, signals: {...} })
                           ↓
MITALI DECISION INTELLIGENCE ENGINE (Temporal + Cross-Sensor + Cross-Station + Persistence + Health)
                           ↓
WEATHER vs SENSOR CLASSIFICATION (genuine_weather | sensor_fault | uncertain)
                           ↓
MULTI-FACTOR TRUST SCORE (0 to 100 Scale)
                           ↓
EXPLANATION GENERATION (Evidence-grounded rationale)
                           ↓
CORRECTION ENGINE (Immutable raw telemetry preserved; human-in-the-loop review)
                           ↓
DIGITAL TWIN & SENSOR HEALTH (Exponential moving averages, degradation tracking)
                           ↓
PREDICTIVE MAINTENANCE QUEUE (Prioritized dispatching: LOW, MEDIUM, HIGH, CRITICAL)
                           ↓
VALIDATED DISASTER RISK LAYER (Gated: sensor faults and uncertain anomalies strictly blocked)
                           ↓
CITIZEN PUBLIC SAFETY ADVISORY (Sanitized: internal sensor IDs, ML scores, and model names suppressed)
                           ↓
FASTAPI REST & WEBSOCKET ENGINE (/api/*, /ws/live)
                           ↓
REACT FRONTEND DASHBOARD (Command Center, Station Map, Digital Twin, Cascade Simulator, Citizen Safety)
```

---

## 2. Database Schema (Supabase PostgreSQL)

The database schema is defined using SQLAlchemy ORM models in `backend/app/models/` and registered with PostgreSQL:

1. **`readings`**: Raw, immutable telemetry records.
   - `reading_id` (VARCHAR PK): Deterministic 24-char SHA-256 hash.
   - `station_id` (VARCHAR): Disambiguated automated weather station ID.
   - `timestamp` (TIMESTAMP): UTC observation timestamp.
   - Nullable measurement channels: `temperature`, `humidity`, `pressure`, `wind_speed`, `wind_direction`, `rainfall`, `solar_radiation`.
   - Geographic metadata: `latitude`, `longitude`, `area`, `elevation`.
   - Provenance: `source`, `quality_flag`.
2. **`stations`**: Unique physical station directory.
   - `station_id` (VARCHAR PK), `name`, `latitude`, `longitude`, `elevation`, `area`, `status`, `created_at`.
3. **`anomalies`**: ML and Decision Intelligence outputs.
   - `anomaly_id` (VARCHAR PK), `reading_id`, `station_id`, `timestamp`, `is_anomaly`, `anomaly_score`, `model_name`, `statistical_score`, `isolation_forest_score`, `autoencoder_score`, `decision`, `fault_type`, `trust_score`, `confidence`, `explanation`, `created_at`.
4. **`corrections`**: Operational data corrections.
   - `correction_id` (VARCHAR PK), `reading_id`, `station_id`, `parameter`, `raw_value`, `suggested_value`, `confidence`, `reason`, `review_status` (`pending`, `accepted`, `rejected`, `reviewed`), `reviewed_by`, `reviewed_at`, `timestamp`.
5. **`sensor_health`**: Digital Twin status.
   - `health_id` (VARCHAR PK), `station_id` (UNIQUE), `recent_health_score`, `historical_health_score`, `total_readings`, `anomaly_count`, `fault_count`, `last_fault_type`, `maintenance_priority`, `updated_at`.
6. **`maintenance_queue`**: Field technician tasks.
   - `maintenance_id` (VARCHAR PK), `station_id`, `priority`, `status`, `issue_description`, `fault_type`, `recommended_action`, `created_at`, `resolved_at`.
7. **`risk_events`**: Validated disaster risks.
   - `risk_id` (VARCHAR PK), `area`, `risk_level` (`LOW`, `MEDIUM`, `HIGH`), `event_type`, `confidence`, `trigger_reading_id`, `supporting_stations`, `public_message`, `safety_guidance`, `advisory_status`, `created_at`.
8. **`cascade_events`**: Illustrative simulation records.

---

## 3. Real-Data Ingestion & Integrity Rules

- **Streaming Line-by-Line**: Processes raw JSONL files via generator `stream_jsonl` without loading multi-hundred-megabyte files into RAM. Reconstructs line-split records seamlessly.
- **NaN → NULL Conversion**: All float `NaN` values are converted to Python `None` and stored as SQL `NULL`.
- **Deterministic Reading ID**:
  $$\text{reading\_id} = \text{SHA256}(\text{physical\_station\_id} + \text{"\_"} + \text{timestamp})[:24]$$
- **Bhadar Dam Disambiguation**:
  - `Bhadar_Dam_Rajkot` (Lat ≈ 21.8100, Lon ≈ 70.7689)
  - `Bhadar_Dam_Aravalli` (Lat ≈ 23.3250, Lon ≈ 73.6917)
- **Restartability & Idempotency**: Batch insertion leverages PostgreSQL `ON CONFLICT (reading_id) DO NOTHING` via `sqlalchemy.dialects.postgresql.insert`.
- **Raw File Immutability**: Source files are read-only and strictly unmodified.

---

## 4. ML Anomaly Detection Integration

Pre-trained model artifacts authored by Manan are loaded once at application startup (`backend/app/services/ml_service.py`):
- **Isolation Forest**: `models/isolation_forest/model.joblib`
- **Tabular Autoencoder**: `models/autoencoder/model.pt` (PyTorch weights), `scaler.joblib`, `imputer.joblib`, `state.json` (75 input features, threshold 0.100749)
- **Statistical Detector**: Baseline z-score and moving deviation metrics.
- **Hybrid Fusion Engine**: Evaluates multi-signal evidence and returns:
  ```json
  {
    "anomaly": true,
    "anomaly_score": 0.88,
    "model": "hybrid",
    "signals": {
      "statistical": 0.85,
      "isolation_forest": 0.89,
      "autoencoder": 0.90
    }
  }
  ```

---

## 5. Decision Intelligence & Critical Responsibility Separation

**Responsibility Boundary**:
- **ML Models**: Answer *“Is this observation statistically and structurally anomalous?”*
- **Decision Intelligence Layer**: Answers *“Is this anomaly authentic extreme weather or an instrumentation fault?”*

**Evidence Dimensions**:
1. **Temporal Consistency**: Rate of change ($\Delta T / \Delta t$). Physical limits reject sudden spikes $>12^\circ\text{C}/\text{hr}$.
2. **Cross-Station Consistency**: Regional neighbor consensus. Queries other stations within regional proximity ($\pm 2\text{ hours}$). If neighbors confirm extreme heat, authentic weather is validated. If neighbors report normal conditions, sensor fault is diagnosed.
3. **Cross-Sensor Consistency**: Thermodynamic atmospheric relationships (e.g. extreme heat with saturated humidity without rain).
4. **Persistence**: Identification of frozen sensors (identical repetitive values).
5. **Historical Sensor Health**: Station reliability history.

**Decisions**:
- `genuine_weather`
- `sensor_fault` (Fault types: `temperature_spike`, `temperature_drift`, `frozen_sensor`, `dropout`, `abrupt_jump`, `multivariate_inconsistency`)
- `uncertain` (Ambiguous corroboration; gated for operator review)

---

## 6. Trust Score Formulation

The Trust Score (0 to 100) is **never** defined merely as $100 \times (1 - \text{anomaly\_score})$.
- **Genuine Extreme Weather** confirmed by regional peers retains a **HIGH Trust Score** (85–95+), because the sensor accurately recorded atmospheric reality.
- **Sensor Faults** (unsupported spikes, frozen sensors) produce a **LOW Trust Score** (5–25).
- **Uncertain Anomalies** produce a **MODERATE Trust Score** (40–60).

---

## 7. Disaster Risk & Citizen Public Safety

- **Strict Gating**:
  - `sensor_fault` $\to$ **BLOCKS** disaster risk assessment.
  - `uncertain` $\to$ **BLOCKS** automatic public alerts.
  - Only validated `genuine_weather` events can trigger risk assessment (`LOW`, `MEDIUM`, `HIGH`).
- **Citizen Safety Sanitization**:
  The `/api/public/risk/{area}` endpoint strips internal diagnostic fields (`anomaly_score`, `model`, `station_id`, `fault_code`) and returns actionable safety instructions.

---

## 8. Historical Replay & Illustrative Cascade Scenarios

- **Historical Replay** (`/api/replay/*`): Streams stored database observations in chronological order through the full pipeline, broadcasting live updates via WebSocket `/ws/live`. Controls: `start`, `pause`, `resume`, `reset`, `speed`.
- **Three Illustrative Cascade Scenarios** (`/api/cascade/{id}`):
  - **Scenario A (Faulty Extreme)**: 55°C spike $\to$ ML Anomaly $\to$ Sensor Fault $\to$ Low Trust $\to$ Correction Proposed $\to$ Disaster Risk Blocked.
  - **Scenario B (Genuine Extreme)**: Multi-station 44°C heatwave $\to$ ML Anomaly $\to$ Genuine Weather $\to$ High Trust $\to$ HIGH Disaster Risk $\to$ Public Safety Alert Issued.
  - **Scenario C (Uncertain)**: Ambiguous thermal jump without peer coverage $\to$ ML Anomaly $\to$ Uncertain $\to$ Moderate Trust $\to$ Held for Operator Review $\to$ No Public Alarm.

---

## 9. FastAPI REST & WebSocket Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status |
| `GET` | `/api/summary` | Command Center summary metrics |
| `GET` | `/api/stations` | List all weather stations |
| `GET` | `/api/stations/{id}` | Single station details |
| `GET` | `/api/stations/{id}/readings` | Station historical observations |
| `GET` | `/api/stations/{id}/health` | Digital Twin health telemetry |
| `GET` | `/api/anomalies` | List detected anomalies |
| `GET` | `/api/anomalies/{id}` | Anomaly investigation dossier |
| `POST` | `/api/inference` | Execute end-to-end pipeline on observation |
| `GET` | `/api/maintenance` | Predictive maintenance task queue |
| `POST` | `/api/corrections/{id}/{action}` | Human review (`accept`, `reject`, `review`) |
| `GET` | `/api/risks` | List validated disaster risks |
| `GET` | `/api/risks/{id}` | Specific disaster risk details |
| `GET` | `/api/public/risk/{area}` | Citizen-safe public advisory |
| `GET` | `/api/cascade/{id}` | Illustrative cascade walkthroughs |
| `POST` | `/api/replay/{start,pause,resume,reset,speed}` | Historical replay controls |
| `WS` | `/ws/live` | Real-time WebSocket event stream |

---

## 10. Verification & Test Suite

Run the full automated test suite:

```bash
# Python compilation check
python -m compileall backend

# Automated Pytest suite (Ingestion & End-to-End Scenarios)
pytest tests/test_ingestion.py tests/test_end_to_end_pipeline.py

# Database integrity verification
python scripts/audit_database.py

# Frontend production build
cd frontend && npm run build
```
