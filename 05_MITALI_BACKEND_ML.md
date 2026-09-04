# SkyGuard AI --- Mitali Execution Plan

## Role

**Primary:** Backend\
**Secondary:** ML integration + EDA

## Mission

Turn all independent modules into one running system.

## Phase 0 --- Architecture

Own: - repository integration, - backend structure, - API contract, -
database contract.

## Backend structure

``` text
backend/app/
├── main.py
├── api/
├── models/
├── schemas/
├── services/
├── websocket/
├── database/
└── core/
```

## Phase 1 --- Data ingestion contract

FastAPI must accept:

``` json
{
  "station_id": "AWS-104",
  "timestamp": "...",
  "temperature": 31.2,
  "pressure": 1004.1,
  "humidity": 48.2
}
```

Validate with Pydantic.

## Phase 2--5 --- ML integration

Create:

``` text
ml/integration/inference_service.py
```

The backend should call one interface.

Example:

``` python
result = inference_service.predict(reading, context)
```

Do not put model-specific logic in API routes.

## Phase 6 --- Reasoning engine

Implement:

``` text
Temporal consistency
Cross-sensor consistency
Cross-station consistency
Persistence
ML evidence
Historical health
```

Output:

``` text
weather
sensor fault
uncertain
```

## Phase 7 --- Trust + explanation

Build:

``` text
trust_service.py
explanation_service.py
fault_classifier.py
```

The explanation must come from structured evidence.

## Phase 8 --- Digital Twin

Create service:

``` text
digital_twin_service.py
```

Update: - health, - trend, - fault count, - trust, - maintenance
priority.

## Database

Use PostgreSQL/Supabase.

Core tables:

``` text
stations
sensors
readings
anomalies
corrections
sensor_health
maintenance_queue
cascade_events
audit_log
```

## Correction workflow

``` text
anomaly
 ↓
suggestion
 ↓
human action
 ↓
audit log
```

Never overwrite raw data.

## Phase 9 --- REST API

Implement:

``` text
GET /api/stations
GET /api/stations/{id}
GET /api/stations/{id}/readings
GET /api/stations/{id}/health
GET /api/anomalies
GET /api/anomalies/{id}
GET /api/maintenance
POST /api/readings
POST /api/inference
POST /api/corrections/{id}/accept
POST /api/corrections/{id}/reject
POST /api/corrections/{id}/review
GET /api/cascade/{id}
```

## Phase 10 --- WebSockets

Implement:

``` text
/ws/live
```

Events:

``` text
reading
anomaly
trust_update
digital_twin_update
maintenance_update
cascade_ready
```

## Replay engine

Implement:

``` text
POST /api/replay/start
POST /api/replay/stop
```

Replay should be deterministic.

## Phase 11 --- Cascade

Build:

``` text
cascade_service.py
```

Inputs: - original reading, - suggested corrected reading, - simplified
downstream rule.

Outputs:

``` text
without_skyguard
with_skyguard
impact_summary
```

Always label the simulation illustrative.

## Phase 12 --- Integration

Mitali should own the full pipeline test:

``` text
reading
→ validation
→ feature
→ ML
→ reasoning
→ trust
→ correction
→ database
→ digital twin
→ maintenance
→ WebSocket
→ frontend
```

## Final backend acceptance test

One command should start: - backend, - database, - replay service, -
required dependencies.

## Mitali's success criterion

The project should not have "ML code," "frontend code," and "backend
code" sitting separately.

Mitali's job is to make them behave as **one product**.
