# SkyGuard AI — Phase 1: Backend Foundation & Weather Data Ingestion

## 1. Objective

The primary objective of **Phase 1** is to establish a rock-solid, production-ready backend foundation for SkyGuard AI. This phase implements robust weather reading ingestion, structural and data-type validation, persistent database storage, and retrieval mechanisms while preserving the immutable historical integrity of raw meteorological telemetry.

Phase 1 deliberately focuses **exclusively** on transport, validation, and persistence, keeping backend interfaces completely decoupled from subsequent ML anomaly detection, fault injection, decision intelligence, and disaster risk assessment modules.

---

## 2. Architecture & Data Flow

```text
        CLIENT / TELEMETRY SOURCE
                   │
                   ▼
           POST /api/readings
                   │
                   ▼
         Pydantic Schema Validation
      (Structure, Datatypes, Ranges)
                   │
                   ▼
           Ingestion Service
    (Duplicate Check, Immutability)
                   │
                   ▼
         Relational Database (SQLAlchemy)
     (`readings` table: Immutable Raw Data)
                   │
                   ▼
         Stored Reading Record
                   │
                   ▼
        HTTP 201 Created Response
```

### Retrieval Flow:
```text
CLIENT / DOWNSTREAM SERVICE (ML Pipeline)
                   │
                   ▼
     GET /api/stations/{id}/readings
                   │
                   ▼
           Ingestion Service
                   │
                   ▼
         Relational Database
                   │
                   ▼
    Historical Readings Array (JSON)
```

---

## 3. API Endpoints

| Method | Endpoint | Status Code | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | `200 OK` | Root service status and version display. |
| `GET` | `/health` | `200 OK` | Operational readiness health check. |
| `POST` | `/api/readings` | `201 Created` | Ingest and persist a new immutable raw weather reading. |
| `GET` | `/api/stations/{id}/readings` | `200 OK` | Retrieve historical readings for an automated weather station. |
| `GET` | `/api/readings/{reading_id}` | `200 OK` | Fetch an individual observation record by reading ID. |
| `GET` | `/docs` | `200 OK` | Interactive Swagger / OpenAPI documentation UI. |
| `GET` | `/openapi.json` | `200 OK` | Machine-readable OpenAPI 3.1 specification schema. |

---

## 4. Reading Schema (Canonical 16-Field Contract)

The ingestion schema strictly honors the Phase-0 inter-module data contract:

```python
class ReadingCreate(BaseModel):
    reading_id: str          # Unique observation identifier (non-empty)
    station_id: str          # Automated weather station identifier (non-empty)
    timestamp: datetime      # UTC ISO 8601 observation timestamp
    temperature: float     # Ambient temperature in °C (extreme values valid)
    pressure: float        # Barometric pressure in hPa
    humidity: float        # Relative humidity percentage (0.0 to 100.0 %)
    wind_speed: float      # Wind speed in m/s (>= 0.0)
    wind_direction: float  # Wind direction in degrees (0.0 to 360.0°)
    rainfall: float        # Precipitation accumulation in mm (>= 0.0)
    solar_radiation: float # Solar irradiance in W/m² (>= 0.0)
    latitude: float        # Latitude in decimal degrees (-90.0 to 90.0)
    longitude: float       # Longitude in decimal degrees (-180.0 to 180.0)
    area: str              # Regional or municipal administrative area
    elevation: float       # Elevation above sea level in meters
    source: str            # Telemetry source indicator (default: "weather_source")
    quality_flag: str      # Data quality flag (default: "valid")
```

---

## 5. Validation Rules

1. **Mandatory Fields**: All 16 fields must be present and non-null in the payload.
2. **Type Coercion & Checking**: Strict numeric and datetime parsing. Strings passed for numeric fields or invalid date formats immediately trigger `HTTP 422 Unprocessable Content`.
3. **Geographic Boundaries**: `latitude` bounded within `[-90.0, 90.0]`; `longitude` bounded within `[-180.0, 180.0]`.
4. **Physical Range Sanity**: `humidity` in `[0.0, 100.0]`, `wind_direction` in `[0.0, 360.0]`, `rainfall >= 0.0`, `wind_speed >= 0.0`, `solar_radiation >= 0.0`.
5. **CRITICAL INVARIANT — Extreme Weather Acceptance**:
   * Validation answers: *"Is this payload structurally and syntactically valid?"*
   * Validation does **NOT** decide: *"Is this observation genuine or faulty?"*
   * A reading of `temperature = 55.0°C` is physically extreme, but structurally valid and **must be accepted with HTTP 201 Created**. Distinguishing genuine meteorological events from sensor malfunctions is exclusively the responsibility of subsequent ML and reasoning modules.

---

## 6. Database Model (`backend/app/models/reading.py`)

Persistent storage is implemented via SQLAlchemy ORM, targeting SQLite for local development and PostgreSQL/Supabase for production:

* **Table Name**: `readings`
* **Primary Key**: `reading_id` (`String`, unique, indexed)
* **Indexes**:
  * `station_id` (`String`, indexed)
  * `timestamp` (`DateTime`, indexed)
  * Composite Index: `ix_readings_station_timestamp` on `(station_id, timestamp)` for high-speed time-series queries.
* **Immutability Principle**: Raw observation telemetry is an immutable historical record. No update or delete operations are exposed.

---

## 7. Ingestion Service (`backend/app/services/ingestion_service.py`)

The ingestion service decouples API transport from database operations:
* `create_reading(reading_in, db)`: Checks whether `reading_id` already exists. If found, raises `DuplicateReadingError` which the API maps to `HTTP 409 Conflict`. Otherwise, commits the new record and returns the persisted model.
* `get_readings_by_station(station_id, db, start_time, end_time)`: Filters readings by station and optional UTC time window, ordered chronologically.
* `get_reading_by_id(reading_id, db)`: Retrieves a specific reading record or returns `None`.

---

## 8. Error Handling

All client and server errors return structured, non-leaking JSON payloads:

* **409 Conflict (Duplicate Reading ID)**:
  ```json
  {
    "detail": {
      "error": "duplicate_reading",
      "message": "Reading with reading_id 'R123' already exists"
    }
  }
  ```
* **404 Not Found (Missing Reading)**:
  ```json
  {
    "detail": {
      "error": "reading_not_found",
      "message": "No reading found for reading_id 'DOES-NOT-EXIST'"
    }
  }
  ```
* **422 Unprocessable Content (Validation Failure)**: Standard FastAPI validation schema detailing specific violating fields and rules.
* **500 Internal Server Error**: Global exception handler masks database details, logs stack traces securely, and returns a safe error message.

---

## 9. Automated Testing

Automated test suite is located in `tests/test_ingestion.py` and executed via `pytest`:
1. `test_1_health_endpoint`: Verifies `/health` returns `{"status": "ok", "service": "skyguard-backend"}`.
2. `test_root_endpoint`: Verifies `/` returns running status.
3. `test_2_valid_weather_reading_accepted`: Verifies successful ingestion with `201 Created`.
4. `test_3_invalid_missing_field_rejected`: Verifies missing required field triggers `422`.
5. `test_4_invalid_datatype_rejected`: Verifies invalid data types and out-of-range coordinates trigger `422`.
6. `test_5_duplicate_reading_rejected`: Verifies duplicate `reading_id` triggers `409 Conflict`.
7. `test_6_stored_reading_can_be_retrieved_by_station`: Verifies multi-station time-series retrieval.
8. `test_stored_reading_retrieval_by_id`: Verifies single record lookup and `404` behavior.
9. `test_7_extreme_weather_reading_accepted`: Explicitly tests `temperature = 55.0°C` returning `201 Created`.
10. `test_8_raw_reading_remains_unchanged_after_retrieval`: Asserts field-by-field raw data immutability.

---

## 10. How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
# Copies default local configuration with SQLite
cp .env.example .env
```

### 3. Run FastAPI Application
```bash
python -m uvicorn backend.app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

---

## 11. Request & Response Examples

### Example 1: Ingest Valid Reading
**Request**:
`POST /api/readings`
```json
{
  "reading_id": "R123",
  "station_id": "AWS-104",
  "timestamp": "2026-09-04T10:00:00",
  "temperature": 31.2,
  "pressure": 1004.1,
  "humidity": 48.2,
  "wind_speed": 12.4,
  "wind_direction": 220.0,
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

**Response (`201 Created`)**:
```json
{
  "message": "Reading accepted and stored",
  "reading": {
    "reading_id": "R123",
    "station_id": "AWS-104",
    "timestamp": "2026-09-04T10:00:00",
    "temperature": 31.2,
    "pressure": 1004.1,
    "humidity": 48.2,
    "wind_speed": 12.4,
    "wind_direction": 220.0,
    "rainfall": 0.0,
    "solar_radiation": 650.0,
    "latitude": 28.61,
    "longitude": 77.21,
    "area": "Delhi",
    "elevation": 216.0,
    "source": "weather_source",
    "quality_flag": "valid"
  }
}
```

### Example 2: Ingest Extreme Weather Reading (Accepted)
**Request**:
`POST /api/readings`
```json
{
  "reading_id": "EXTREME-001",
  "station_id": "AWS-104",
  "timestamp": "2026-09-04T12:00:00",
  "temperature": 55.0,
  "pressure": 1000.0,
  "humidity": 20.0,
  "wind_speed": 10.0,
  "wind_direction": 180.0,
  "rainfall": 0.0,
  "solar_radiation": 900.0,
  "latitude": 28.61,
  "longitude": 77.21,
  "area": "Delhi",
  "elevation": 216.0,
  "source": "test",
  "quality_flag": "valid"
}
```

**Response (`201 Created`)**:
```json
{
  "message": "Reading accepted and stored",
  "reading": {
    "reading_id": "EXTREME-001",
    "station_id": "AWS-104",
    "timestamp": "2026-09-04T12:00:00",
    "temperature": 55.0,
    "pressure": 1000.0,
    "humidity": 20.0,
    "wind_speed": 10.0,
    "wind_direction": 180.0,
    "rainfall": 0.0,
    "solar_radiation": 900.0,
    "latitude": 28.61,
    "longitude": 77.21,
    "area": "Delhi",
    "elevation": 216.0,
    "source": "test",
    "quality_flag": "valid"
  }
}
```

### Example 3: Invalid Request (Missing Field / Bad Type)
**Request**:
`POST /api/readings`
```json
{
  "reading_id": "R999",
  "station_id": "AWS-104",
  "temperature": "extremely_hot"
}
```

**Response (`422 Unprocessable Content`)**:
Detailed Pydantic schema validation errors listing missing fields (`timestamp`, `pressure`, etc.) and invalid float conversion for `temperature`.

---

## 12. Phase 1 Limitations

* **No ML Anomaly Detection**: Phase 1 does not flag observations as statistical anomalies.
* **No Decision Reasoning**: Phase 1 does not classify readings as `genuine_weather` or `sensor_fault`.
* **No Trust Score**: Operational dependability scores are not calculated.
* **No Value Imputation / Correction**: Values are recorded strictly as reported by the telemetry source.
* **No Disaster Risk Engine**: No risk hazard scores or citizen safety views are active yet.
* **No WebSocket Streaming**: Telemetry is ingested via REST HTTP requests.
* **No Replay Controls**: Streaming replay engines will be integrated in subsequent phases.

---

## 13. What Phase 2 Will Consume from Phase 1

Phase 2 (Synthetic Fault Injection) and Phase 3 (Feature Engineering & Anomaly Detection) will directly build on this foundation:
1. **Clean Database Feed**: The `readings` table provides an immutable source of historical baseline observations.
2. **Standardized Ingestion Endpoint**: Fault-injected synthetic observations will enter the system through `POST /api/readings`.
3. **Retrieval API**: Feature extractors and anomaly adapters will fetch time-series windows via `GET /api/stations/{id}/readings`.
