# SkyGuard AI --- Implementation & Phase Flow

## 1. Project Overview

**SkyGuard AI** is an AI-powered weather-sensor reliability system.

The system does not simply ask:

> "Is this weather reading anomalous?"

It asks:

> "Is the weather actually unusual, or is the sensor lying?"

It then:

1.  detects suspicious readings,
2.  combines statistical and ML evidence,
3.  compares the reading with other weather variables,
4.  compares it with nearby stations,
5.  decides whether the event is probably genuine weather or a sensor
    fault,
6.  produces a 0--100 Trust Score,
7.  explains the decision,
8.  suggests a safer replacement value,
9.  keeps the raw reading unchanged,
10. tracks sensor health using a Digital Twin,
11. prioritizes maintenance,
12. and shows the downstream impact that could have occurred if the bad
    reading had not been caught.

The uploaded blueprint defines the core architecture, dataset strategy,
six features, X-Factor, technology stack, phased build plan, demo and
validation strategy. This document converts that blueprint into a
practical six-member implementation plan.

------------------------------------------------------------------------

# 2. Team Division

  Member         Primary Responsibility   Secondary Responsibility
  -------------- ------------------------ --------------------------
  **Manan**      ML                       EDA
  **Muskan**     ML                       Data Collection
  **Medhvi**     Frontend                 EDA
  **Neha**       Data Collection          EDA
  **Mitali**     Backend                  ML + EDA
  **Darshita**   Frontend                 ---

------------------------------------------------------------------------

# 3. Final Product Flow

``` text
REAL WEATHER DATA
        ↓
DATA COLLECTION
        ↓
RAW DATA STORAGE
        ↓
DATA VALIDATION
        ↓
DATA CLEANING
        ↓
EDA
        ↓
FAULT INJECTION
        ↓
FEATURE ENGINEERING
        ↓
STATISTICAL DETECTION
        +
ISOLATION FOREST
        +
AUTOENCODER
        ↓
HYBRID ANOMALY SCORE
        ↓
CONSISTENCY ENGINE
        ↓
 ┌───────────────────────────────┐
 │ Temporal Consistency          │
 │ Cross-Sensor Consistency      │
 │ Cross-Station Consistency     │
 │ Persistence                   │
 └───────────────────────────────┘
        ↓
WEATHER-vs-SENSOR DECISION ENGINE
        ↓
 ┌───────────────────────────────┐
 │ Genuine Weather               │
 │ Sensor Fault                  │
 │ Uncertain / Review Required   │
 └───────────────────────────────┘
        ↓
FAULT CLASSIFICATION
        ↓
TRUST SCORE
        ↓
EXPLANATION
        ↓
SUGGESTED CORRECTION
        ↓
HUMAN APPROVAL
   ↓       ↓       ↓
ACCEPT   REJECT   REVIEW
        ↓
DIGITAL TWIN
        ↓
SENSOR HEALTH TREND
        ↓
PREDICTIVE MAINTENANCE QUEUE
        ↓
CASCADE IMPACT SIMULATOR
        ↓
FASTAPI BACKEND
        ↓
WEBSOCKET REAL-TIME STREAM
        ↓
REACT FRONTEND
        ↓
COMMAND CENTER
MAP
INVESTIGATION
DIGITAL TWIN
MAINTENANCE
CASCADE
```

------------------------------------------------------------------------

# 4. Phase 0 --- Git Repository and Project Setup

## Objective

Before anyone starts coding the actual project, create a shared
engineering environment.

## Owner

**Mitali --- Lead**

All six members participate.

## Repository

``` text
skyguard-ai/
```

## Branches

``` text
main
develop

feature/data-pipeline
feature/eda
feature/fault-injection
feature/ml
feature/backend
feature/frontend
feature/digital-twin
feature/cascade
feature/validation
```

## Repository structure

``` text
skyguard-ai/
│
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── docs/
│   ├── architecture.md
│   ├── implementation.md
│   ├── data-dictionary.md
│   ├── api-contract.md
│   ├── ml-design.md
│   ├── ui-design.md
│   └── validation.md
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── synthetic/
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_temperature_eda.ipynb
│   ├── 03_pressure_eda.ipynb
│   ├── 04_humidity_eda.ipynb
│   ├── 05_fault_injection.ipynb
│   └── 06_model_evaluation.ipynb
│
├── ml/
│   ├── preprocessing/
│   ├── features/
│   ├── detectors/
│   ├── scoring/
│   ├── correction/
│   ├── evaluation/
│   └── artifacts/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── services/
│   │   ├── database/
│   │   └── websocket/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── types/
│   │   └── utils/
│   └── tests/
│
└── simulator/
    ├── replay/
    ├── fault_injector/
    └── cascade/
```

## Git workflow

``` text
Create branch
    ↓
Implement
    ↓
Test locally
    ↓
Commit
    ↓
Push
    ↓
Pull Request
    ↓
Code Review
    ↓
Merge into develop
    ↓
Integration Test
    ↓
main
```

## Phase 0 deliverables

-   GitHub repository
-   README
-   folder structure
-   branch strategy
-   issue board
-   basic backend skeleton
-   basic frontend skeleton
-   Python environment
-   `.env.example`
-   initial architecture diagram
-   initial API contract

## Exit condition

Every member can clone the repository and run the basic project
skeleton.

------------------------------------------------------------------------

# 5. Phase 1 --- Data Collection

## Objective

Collect enough real historical weather data to learn what normal station
behavior looks like.

The source blueprint recommends:

-   public IMD/NOAA weather station records,
-   approximately 10--20 stations,
-   3--6 months,
-   hourly observations,
-   Temperature,
-   Pressure,
-   Humidity.

A single station can support a bare MVP, but multiple stations are
required for the stronger cross-station reasoning story.

## Owners

### Lead

-   Neha

### Support

-   Muskan
-   Manan
-   Mitali

## Required core fields

``` text
station_id
timestamp
temperature
pressure
humidity
latitude
longitude
source
quality_flag
```

Optional:

``` text
station_name
region
elevation
```

## Rule

Never modify raw data.

Store:

``` text
data/raw/
```

and perform transformations into:

``` text
data/interim/
data/processed/
```

## Data collection process

``` text
Identify source
    ↓
Select stations
    ↓
Download data
    ↓
Store raw files
    ↓
Document source
    ↓
Standardize columns
    ↓
Validate timestamps
    ↓
Check missingness
    ↓
Check duplicates
    ↓
Check values
    ↓
Create clean dataset
```

## Deliverables

-   raw dataset
-   station metadata
-   source documentation
-   data dictionary
-   ingestion script
-   validation script
-   cleaned dataset

------------------------------------------------------------------------

# 6. Phase 2 --- EDA

## Owners

-   Neha
-   Manan
-   Medhvi
-   Mitali

## Objective

Understand normal weather behavior before designing the anomaly
detector.

## Questions EDA must answer

1.  What is normal temperature behavior?
2.  What is normal pressure behavior?
3.  What is normal humidity behavior?
4.  What are normal daily patterns?
5.  How different are stations?
6.  How much missing data exists?
7.  How strongly do nearby stations correlate?
8.  Which features could identify sensor faults?
9.  What does normal behavior look like before synthetic fault
    injection?

## Required EDA

### Temperature

-   distribution
-   hourly behavior
-   rolling mean
-   rolling standard deviation
-   station comparison

### Pressure

-   distribution
-   temporal behavior
-   station comparison

### Humidity

-   distribution
-   temporal behavior
-   station comparison

### Cross-sensor

``` text
Temperature ↔ Humidity
Temperature ↔ Pressure
Pressure ↔ Humidity
```

### Cross-station

Compare geographically close stations.

### Missingness

``` text
missing by station
missing by variable
missing by period
```

## EDA deliverables

``` text
01_data_audit.ipynb
02_temperature_eda.ipynb
03_pressure_eda.ipynb
04_humidity_eda.ipynb
data_quality_report.md
station_neighbors.csv
```

## Exit condition

The team can clearly describe what "normal" means for the selected
stations.

------------------------------------------------------------------------

# 7. Phase 3 --- Data Cleaning and Validation Pipeline

## Owner

**Neha**

## Support

Muskan + Mitali

## Validation checks

### Timestamp

Check:

-   invalid timestamps,
-   duplicates,
-   ordering,
-   timezone,
-   gaps.

### Missing values

Check:

-   null count,
-   null percentage,
-   station-level missingness,
-   variable-level missingness.

### Duplicate readings

Use:

``` text
station_id + timestamp
```

as the main uniqueness combination.

### Invalid values

Flag physically impossible or malformed values.

Important:

> Do not automatically delete extreme weather values simply because they
> look unusual.

An extreme value may be real weather.

## Pipeline

``` text
Raw data
    ↓
Schema validation
    ↓
Timestamp validation
    ↓
Duplicate check
    ↓
Missing-value analysis
    ↓
Value validation
    ↓
Quality flags
    ↓
Processed dataset
```

## Exit condition

A clean dataset can be generated reproducibly from the raw files.

------------------------------------------------------------------------

# 8. Phase 4 --- Fault Injection Lab

## Owner

**Muskan**

## Support

-   Neha
-   Manan

The source blueprint uses synthetic fault injection because public
datasets generally do not provide large-scale verified sensor-fault
labels.

## Target

Create approximately:

``` text
500–2,000 synthetic fault events
```

distributed across:

-   stations,
-   variables,
-   durations,
-   severity,
-   fault types.

## Fault types

### 1. Spike

Example:

``` text
31.2
31.4
31.1
55.0  ← fault
31.3
31.2
```

### 2. Slow drift

``` text
31.0
31.2
31.4
31.7
32.1
32.6
33.0
```

### 3. Frozen sensor

``` text
31.8
31.8
31.8
31.8
31.8
31.8
```

### 4. Dropout

``` text
31.8
31.7
NaN
NaN
NaN
31.9
```

### 5. Abrupt jump

``` text
31
31
31
42
42
42
```

### 6. Multivariate inconsistency

Example:

``` text
Temperature:
31 → 42

Pressure:
stable

Humidity:
stable
```

The system should treat this as evidence, not automatically as proof.

### 7. Cross-station inconsistency

One station changes sharply while nearby stations remain normal.

## Ground truth

Every synthetic event must contain:

``` text
event_id
station_id
variable
fault_type
start_timestamp
end_timestamp
original_value
corrupted_value
severity
random_seed
ground_truth
```

## Reproducibility

Use fixed seeds.

Running:

``` text
generate_faults(seed=42)
```

should reproduce the same benchmark.

------------------------------------------------------------------------

# 9. Phase 5 --- Feature Engineering

## Owner

**Manan**

## Support

-   Muskan
-   Neha
-   Mitali

## Core inputs

``` text
temperature
pressure
humidity
```

## Rolling features

``` text
rolling_mean_3
rolling_std_3
rolling_mean_6
rolling_std_6
rolling_mean_24
rolling_std_24
```

## Change features

``` text
delta_1
delta_3
delta_6
rate_of_change
```

## Time features

``` text
hour
day_of_week
day_of_year
month
sin_hour
cos_hour
```

## Cross-sensor features

``` text
temperature_change
pressure_change
humidity_change
temperature_humidity_relation
pressure_temperature_relation
```

## Cross-station features

``` text
neighbor_mean
neighbor_median
neighbor_std
difference_from_neighbor_mean
```

## Critical rule

Training and production inference must use the same feature code.

Do not create features manually in notebooks and recreate them
differently in FastAPI.

------------------------------------------------------------------------

# 10. Phase 6 --- Statistical Baseline

## Owner

**Manan**

## Objective

Build a working detector before ML.

This gives the team:

-   baseline performance,
-   explainability,
-   fallback behavior,
-   debugging reference.

## Methods

### Z-score

``` text
z = (x - mean) / standard_deviation
```

### Rolling Z-score

Compare the current value with recent local behavior.

### EWMA

Detect changes in a time series using exponentially weighted history.

### Persistence

A suspicious value that continues across several observations should be
treated differently from a single isolated point.

## Output

``` json
{
  "rule_flags": [],
  "statistical_score": 0.82,
  "persistence_score": 0.21
}
```

------------------------------------------------------------------------

# 11. Phase 7 --- Machine Learning

## Owners

-   Manan
-   Muskan

## Support

Mitali

The source blueprint recommends:

``` text
Isolation Forest
+
Autoencoder
```

## 7.1 Isolation Forest

Purpose:

Detect unusual feature combinations without requiring all fault types to
be manually classified.

Input:

``` text
temperature
pressure
humidity
rolling features
change features
neighbor features
```

Output:

``` text
anomaly_score
is_anomaly
```

Thresholds should be selected using validation data.

------------------------------------------------------------------------

# 12. Phase 8 --- Autoencoder

## Owner

**Muskan**

## Support

Manan

Train primarily on clean/normal data.

Architecture:

``` text
Input
  ↓
Encoder
  ↓
Latent representation
  ↓
Decoder
  ↓
Reconstructed input
```

Normal:

``` text
low reconstruction error
```

Anomalous:

``` text
high reconstruction error
```

Output:

``` text
reconstruction_error
anomaly_score
```

The model's raw anomaly score should not automatically be described as
calibrated probability.

------------------------------------------------------------------------

# 13. Phase 9 --- Hybrid ML Detector

## Owners

Manan + Muskan

Combine:

``` text
Statistical detector
        +
Isolation Forest
        +
Autoencoder
```

Example:

``` text
Rule evidence       = 0.90
Isolation Forest    = 0.94
Autoencoder         = 0.88

Hybrid anomaly      = HIGH
```

The final combination must be evaluated rather than chosen only because
it looks good in one demo.

## Output contract

``` json
{
  "is_anomaly": true,
  "anomaly_score": 0.91,
  "statistical_score": 0.90,
  "isolation_score": 0.94,
  "autoencoder_score": 0.88
}
```

------------------------------------------------------------------------

# 14. Phase 10 --- Consistency Engine

## Owner

**Mitali**

## Support

Manan + Muskan + Neha

This is where SkyGuard becomes more than a normal anomaly detector.

## 10.1 Temporal consistency

Ask:

> Did the sensor change in a way consistent with its recent history?

## 10.2 Cross-sensor consistency

Ask:

> Do temperature, pressure and humidity support the same weather event?

## 10.3 Cross-station consistency

Ask:

> Did geographically close stations observe a similar event?

## 10.4 Persistence

Ask:

> Did the suspicious behavior continue?

------------------------------------------------------------------------

# 15. Phase 11 --- Weather-vs-Sensor Decision Engine

## Owner

**Mitali**

## Inputs

``` text
current reading
historical context
ML scores
statistical scores
cross-sensor evidence
cross-station evidence
persistence
sensor health
```

## Output

``` text
GENUINE_WEATHER
SENSOR_FAULT
UNCERTAIN
```

## Example --- Sensor fault

``` text
AWS-104

Temperature:
31.2°C → 55.0°C

Nearby stations:
30.8°C–32.1°C

Humidity:
normal

Pressure:
normal

ML:
high anomaly

Persistence:
low
```

Decision:

``` text
PROBABLE SENSOR FAULT
```

## Example --- Genuine weather

``` text
Station A: 42°C
Station B: 43°C
Station C: 41.5°C
Station D: 42.7°C

Other variables support event.

Decision:

GENUINE WEATHER
```

------------------------------------------------------------------------

# 16. Phase 12 --- Fault Classifier

## Owners

Mitali + Manan

## Fault classes

``` text
SPIKE
DRIFT
FROZEN
DROPOUT
ABRUPT_JUMP
MULTIVARIATE_INCONSISTENCY
UNKNOWN
```

The classifier can initially be rule/evidence based.

Do not force another ML model into the system unless validation shows it
is useful.

------------------------------------------------------------------------

# 17. Phase 13 --- Trust Score

## Owners

Mitali + Manan

The Trust Score answers:

> "How much should we trust this reading right now?"

Range:

``` text
0–100
```

Suggested interpretation:

``` text
90–100 → Very High Trust
75–89  → High Trust
50–74  → Moderate
25–49  → Low
0–24   → Very Low
```

## Evidence components

``` text
Temporal consistency
Cross-sensor agreement
Cross-station agreement
ML anomaly evidence
Historical sensor health
Missingness
Persistence
```

Example:

``` text
Temporal consistency       +10
Cross-sensor agreement     +05
Cross-station agreement    +00
ML anomaly evidence        -45
Persistence                -20
Historical health          -12
--------------------------------
Trust Score                 18
```

These weights are starting assumptions and must be validated.

------------------------------------------------------------------------

# 18. Phase 14 --- Explainability

## Owner

**Mitali**

## Objective

Every decision must answer:

``` text
What happened?
Why is it suspicious?
What evidence supports the decision?
What does the system recommend?
```

Example:

> Temperature jumped from 31.2°C to 55°C. Nearby stations remained
> between 30.8°C and 32.1°C. Humidity and pressure did not show
> corresponding changes. ML detectors marked the observation anomalous.
> The sensor has also shown repeated recent anomalies.

Result:

``` text
Probable sensor spike
Confidence: high
Trust: 18/100
```

The explanation should be generated from structured evidence.

------------------------------------------------------------------------

# 19. Phase 15 --- Suggested Correction

## Owner

**Mitali**

## Rule

Never silently modify the original observation.

Store both:

``` text
raw_value
suggested_value
```

## Possible correction methods

### Spike

Use:

``` text
local trend
+
neighbor station estimate
```

### Dropout

Use:

``` text
interpolation
or
neighbor estimate
```

### Frozen

Use:

``` text
recent trend
+
neighbor information
```

### Cross-station inconsistency

Use:

``` text
neighbor median
```

## Output

``` json
{
  "original_value": 55.0,
  "suggested_value": 31.8,
  "method": "neighbor_and_local_estimate",
  "confidence": 0.91
}
```

------------------------------------------------------------------------

# 20. Phase 16 --- Human Approval

## Owner

Backend: Mitali

## Frontend

Medhvi + Darshita

Actions:

``` text
ACCEPT
REJECT
REVIEW
```

## Accept

The suggested value becomes the approved operational value while the raw
value remains preserved.

## Reject

The correction is rejected.

## Review

The event remains unresolved.

Every action is recorded in the audit log.

------------------------------------------------------------------------

# 21. Phase 17 --- Digital Twin

## Owner

**Mitali**

## Support

Manan + Neha

The Digital Twin is the long-term health profile of each sensor.

## Difference between Trust and Health

### Trust Score

> How much do we trust the current reading?

### Health Score

> How healthy does the sensor appear over time?

They must not be treated as identical.

## Digital Twin data

``` text
station_id
sensor_id
current_value
current_trust
health_score
fault_count_7d
fault_count_30d
last_fault
fault_history
trend
maintenance_priority
```

Example:

``` json
{
  "station_id": "AWS-104",
  "health_score": 62,
  "trust_score": 18,
  "trend": "DECLINING",
  "fault_count_7d": 4,
  "fault_count_30d": 11,
  "maintenance_priority": "HIGH"
}
```

------------------------------------------------------------------------

# 22. Phase 18 --- Predictive Maintenance Queue

## Owner

Mitali

## Support

Manan + Neha

Rank sensors using:

``` text
current trust
health trend
fault frequency
fault severity
recency
persistence
data availability
```

Example:

``` text
#1 AWS-104
HIGH
Health: 62
Trust: 18
Trend: Declining
Faults: 11 / 30 days
Reason: repeated temperature spikes + degradation

#2 AWS-117
MEDIUM
Health: 71
Trust: 43
Trend: Declining
Reason: repeated dropout
```

------------------------------------------------------------------------

# 23. Phase 19 --- Database

## Owner

**Mitali**

Recommended:

``` text
PostgreSQL / Supabase
```

## Tables

### stations

``` text
id
station_code
name
latitude
longitude
region
created_at
```

### sensors

``` text
id
station_id
sensor_type
status
created_at
```

### readings

``` text
id
sensor_id
timestamp
temperature
pressure
humidity
source
raw_payload
validation_status
created_at
```

### anomalies

``` text
id
reading_id
detected_at
anomaly_score
fault_type
decision
confidence
trust_score
reason_codes
status
```

### corrections

``` text
id
anomaly_id
original_value
suggested_value
method
confidence
decision
reviewed_by
reviewed_at
```

### sensor_health

``` text
id
sensor_id
timestamp
health_score
trust_score
anomaly_count
trend
maintenance_priority
```

### maintenance_queue

``` text
id
sensor_id
priority
priority_score
reason
status
created_at
updated_at
```

### cascade_events

``` text
id
anomaly_id
scenario_type
bad_input
corrected_input
without_skyguard_result
with_skyguard_result
impact_summary
created_at
```

### audit_log

``` text
id
entity_type
entity_id
action
payload
timestamp
```

------------------------------------------------------------------------

# 24. Phase 20 --- Backend

## Owner

**Mitali**

## Technology

``` text
FastAPI
Python
Pydantic
PostgreSQL
```

## Backend services

``` text
ingestion_service
validation_service
feature_service
inference_service
reasoning_service
trust_service
correction_service
digital_twin_service
maintenance_service
cascade_service
replay_service
```

## API

``` text
GET  /api/stations
GET  /api/stations/{id}
GET  /api/stations/{id}/readings
GET  /api/stations/{id}/health
GET  /api/stations/{id}/anomalies

POST /api/readings
POST /api/inference

GET  /api/anomalies
GET  /api/anomalies/{id}

POST /api/corrections/{id}/accept
POST /api/corrections/{id}/reject
POST /api/corrections/{id}/review

GET  /api/maintenance

POST /api/replay/start
POST /api/replay/stop

POST /api/simulator/inject

GET  /api/cascade/{anomaly_id}

WS   /ws/live
```

------------------------------------------------------------------------

# 25. Phase 21 --- Frontend Design

## Owners

-   Medhvi
-   Darshita

## Technology

``` text
React
Vite
Tailwind CSS
Recharts / Plotly
Leaflet
```

The UI should feel like an operational meteorological command center
rather than a generic college dashboard.

## Main navigation

``` text
COMMAND CENTER
STATION MAP
INVESTIGATION
DIGITAL TWINS
MAINTENANCE
CASCADE
SYSTEM HEALTH
```

------------------------------------------------------------------------

# 26. Command Center

## Top cards

``` text
TOTAL STATIONS
HEALTHY
DEGRADING
CRITICAL
ACTIVE ANOMALIES
AVERAGE TRUST
```

## Main areas

### Network map

Show station status.

### Live anomaly feed

Example:

``` text
12:03:14
AWS-104
Temperature spike
Trust: 18
High confidence
```

### Network health

Show distribution of trust and sensor health.

### Maintenance preview

Show top priority sensors.

------------------------------------------------------------------------

# 27. Station Map

Use:

``` text
Leaflet
```

Marker states:

``` text
GREEN  → healthy
AMBER  → suspicious
RED    → critical
```

Clicking a station opens:

``` text
Station ID
Location
Temperature
Pressure
Humidity
Trust
Health
Last anomaly
Status
```

------------------------------------------------------------------------

# 28. Investigation Screen

This is the main analytical screen.

Recommended structure:

``` text
AWS-104
Temperature
PROBABLE SENSOR FAULT

Trust: 18/100
Confidence: 97%

--------------------------------

TIME SERIES

Temperature graph
with anomaly highlighted

--------------------------------

EVIDENCE

✓ Recent history
✕ Cross-station agreement
✕ Cross-sensor consistency
✕ ML normality

--------------------------------

SUGGESTED CORRECTION

55°C → 31.8°C

[ ACCEPT ]
[ REJECT ]
[ REVIEW ]

--------------------------------

CASCADE IMPACT

Run simulation
```

The judge should understand the situation within approximately 10
seconds.

------------------------------------------------------------------------

# 29. Digital Twin UI

Display:

``` text
AWS-104

HEALTH
62/100

CURRENT TRUST
18/100

TREND
DECLINING

7-DAY FAULTS
4

30-DAY FAULTS
11

LAST FAULT
TEMPERATURE SPIKE

MAINTENANCE
HIGH PRIORITY
```

Add:

-   health timeline,
-   fault history,
-   trend chart.

------------------------------------------------------------------------

# 30. Maintenance Queue UI

Columns:

``` text
Priority
Sensor
Health
Trust
Trend
Fault Count
Last Fault
Reason
Action
```

The UI must immediately show which sensor should be fixed first.

------------------------------------------------------------------------

# 31. Phase 22 --- Real-Time Integration

## Owner

**Mitali**

## Frontend support

Darshita + Medhvi

The source blueprint recommends WebSockets for live/replay event
streaming.

## Architecture

``` text
Historical / Synthetic Data
        ↓
Replay Engine
        ↓
FastAPI
        ↓
Inference
        ↓
Reasoning
        ↓
Database
        ↓
WebSocket
        ↓
React
```

## Event flow

``` text
new reading
    ↓
validation
    ↓
inference
    ↓
decision
    ↓
database
    ↓
WebSocket
    ↓
frontend update
```

## Frontend connection states

``` text
LIVE
RECONNECTING
OFFLINE
REPLAY MODE
```

------------------------------------------------------------------------

# 32. Phase 23 --- Replay Engine

## Owner

Mitali

The replay engine is important because the demo can use
historical/synthetic data while appearing live.

Example:

``` text
1 historical hour
→ replayed over 2 minutes
```

Or:

``` text
1 observation
→ emitted every 1–2 seconds
```

The replay must be deterministic.

## Controls

Frontend:

``` text
START
PAUSE
RESUME
RESET
SPEED
```

------------------------------------------------------------------------

# 33. Phase 24 --- Cascade Impact Simulator

## Owner

Mitali

## Frontend

Medhvi + Darshita

This is the X-Factor.

The purpose is to show:

> What could have happened downstream if SkyGuard had not caught the
> faulty reading?

## Example

Fault:

``` text
AWS-104 = 55°C
```

SkyGuard:

``` text
Probable sensor fault
Trust = 18
Suggested = 31.8°C
```

Without SkyGuard:

``` text
55°C enters illustrative downstream rule
        ↓
district average crosses threshold
        ↓
FALSE HEATWAVE ALERT
```

With SkyGuard:

``` text
Suspicious value quarantined
        ↓
Suggested value used
        ↓
NO FALSE HEATWAVE ALERT
```

## Genuine event

``` text
Several nearby stations report extreme temperature
        ↓
cross-station agreement high
        ↓
cross-sensor evidence supportive
        ↓
GENUINE WEATHER
```

Then demonstrate that suppressing the event could delay a real warning.

## Important limitation

The simulator is an illustrative downstream model.

It is not the real IMD forecasting system.

The UI should explicitly state:

> "Illustrative downstream impact simulation --- not an IMD forecasting
> model."

------------------------------------------------------------------------

# 34. Phase 25 --- Frontend + Backend Integration

## Owners

All six.

## Integration order

``` text
Backend health endpoint
        ↓
Frontend dashboard
        ↓
Stations API
        ↓
Station map
        ↓
Anomalies API
        ↓
Investigation screen
        ↓
Digital Twin API
        ↓
Maintenance API
        ↓
Correction API
        ↓
Cascade API
        ↓
WebSocket
```

------------------------------------------------------------------------

# 35. Phase 26 --- Full End-to-End Pipeline

At this point the entire system must work as:

``` text
DATA
 ↓
VALIDATION
 ↓
FEATURES
 ↓
STATISTICAL DETECTOR
 ↓
ISOLATION FOREST
 ↓
AUTOENCODER
 ↓
CONSISTENCY ENGINE
 ↓
WEATHER-vs-SENSOR ENGINE
 ↓
FAULT CLASSIFICATION
 ↓
TRUST SCORE
 ↓
EXPLANATION
 ↓
CORRECTION
 ↓
DATABASE
 ↓
DIGITAL TWIN
 ↓
MAINTENANCE
 ↓
CASCADE
 ↓
WEBSOCKET
 ↓
FRONTEND
```

This is the most important integration checkpoint.

------------------------------------------------------------------------

# 36. Phase 27 --- Validation

## Owner

**Manan**

## Support

-   Muskan
-   Neha
-   Mitali

## Metrics

### Precision

How many detected faults are actually faults?

### Recall

How many actual faults did the system catch?

### F1

Balance between precision and recall.

### False Alarm Rate During Genuine Weather

This is particularly important.

The system should not call every extreme event a sensor failure.

### Detection Latency

Measure:

``` text
fault timestamp
→ detection timestamp
```

Report:

``` text
mean
median
p95
```

### Correction Error

Use:

``` text
MAE
RMSE
```

Compare suggested correction with clean ground truth.

### Early Degradation Warning Time

Measure how early the Digital Twin identifies a deteriorating sensor.

### Cascade Cases

Count demonstrated:

``` text
false alert prevented
genuine alert preserved
```

------------------------------------------------------------------------

# 37. Validation Scenarios

## Test 1 --- Isolated spike

``` text
One station:
55°C

Nearby:
normal
```

Expected:

``` text
SENSOR FAULT
```

## Test 2 --- Genuine heat event

``` text
Several nearby stations:
41–43°C
```

Expected:

``` text
GENUINE WEATHER
```

## Test 3 --- Drift

Expected:

``` text
DEGRADATION
```

## Test 4 --- Flatline

Expected:

``` text
FROZEN SENSOR
```

## Test 5 --- Dropout

Expected:

``` text
DATA / SENSOR FAULT
```

## Test 6 --- Multivariate inconsistency

Expected:

``` text
HIGH SUSPICION / REVIEW
```

depending on supporting evidence.

------------------------------------------------------------------------

# 38. Phase 28 --- Testing

## Unit testing

### Data

-   timestamp parsing,
-   schema validation,
-   missing values,
-   fault generation.

### ML

-   feature generation,
-   model loading,
-   inference,
-   score ranges.

### Backend

-   API,
-   database,
-   corrections,
-   WebSocket.

### Frontend

-   component rendering,
-   API state,
-   error handling,
-   WebSocket updates.

## Integration test

The team must test:

``` text
reading
→ validation
→ features
→ ML
→ reasoning
→ trust
→ correction
→ database
→ Digital Twin
→ maintenance
→ WebSocket
→ frontend
```

------------------------------------------------------------------------

# 39. Phase 29 --- Deployment

## Recommended stack

``` text
Docker
Frontend deployment
Backend deployment
PostgreSQL/Supabase
```

## Deployment architecture

``` text
USER
 ↓
FRONTEND
 ↓
FASTAPI
 ↓
POSTGRESQL
 ↓
ML PIPELINE
```

## Docker

Create:

``` text
Dockerfile.backend
Dockerfile.frontend
docker-compose.yml
```

## Clean machine test

A teammate who did not build the environment should be able to:

``` text
git clone
docker compose up
```

and access the application.

------------------------------------------------------------------------

# 40. Phase 30 --- Final Demo Preparation

## Demo should be deterministic.

Do not rely on random fault injection during the final presentation.

Prepare fixed scenarios.

------------------------------------------------------------------------

# 41. Winning Demo Flow

## Step 1 --- Healthy Network

Open:

``` text
Command Center
```

Show:

``` text
stations green
high trust
healthy sensors
```

## Step 2 --- Inject 55°C Spike

At:

``` text
AWS-104
```

## Step 3 --- Real-Time Detection

Dashboard receives:

``` text
ANOMALY DETECTED
```

## Step 4 --- Investigation

Show:

``` text
Temperature spike
Trust = 18
Confidence = 97%
```

## Step 5 --- Explain

Show:

``` text
Temporal inconsistency
Cross-station mismatch
Cross-sensor mismatch
ML anomaly
```

## Step 6 --- Cascade

Click:

``` text
RUN CASCADE
```

Show:

``` text
WITHOUT SKYGUARD
FALSE HEATWAVE ALERT

WITH SKYGUARD
NO FALSE ALERT
```

## Step 7 --- Correction

Show:

``` text
55°C
↓
31.8°C
```

Buttons:

``` text
ACCEPT
REJECT
REVIEW
```

## Step 8 --- Digital Twin

Open:

``` text
AWS-104
```

Show:

``` text
Health declining
Multiple recent faults
```

## Step 9 --- Maintenance

Show:

``` text
AWS-104 → HIGH PRIORITY
```

## Step 10 --- Genuine Weather

Reset.

Trigger coordinated event.

Show:

``` text
multiple stations agree
↓
GENUINE WEATHER
```

## Step 11 --- Closing

Say:

> "Other systems ask: Is this reading anomalous? SkyGuard asks: Is the
> weather anomalous, or is the sensor lying --- and what would have
> happened if we hadn't caught it?"

------------------------------------------------------------------------

# 42. Team Phase Ownership Matrix

  -------------------------------------------------------------------------------
  Phase         Manan      Muskan     Medhvi     Neha       Mitali     Darshita
  ------------- ---------- ---------- ---------- ---------- ---------- ----------
  Git setup     Support    Support    **Lead**   Support    **Lead**   Support

  Data          Support    **Lead**   Support    **Lead**   Support    ---
  collection                                                           

  Data          Support    Support    Support    **Lead**   Support    ---
  validation                                                           

  EDA           **Lead**   Support    Support    **Lead**   Support    ---

  Fault         Support    **Lead**   ---        Support    ---        ---
  injection                                                            

  Feature       **Lead**   Support    ---        Support    Support    ---
  engineering                                                          

  Statistical   **Lead**   Support    ---        ---        Support    ---
  baseline                                                             

  Isolation     **Lead**   **Lead**   ---        ---        Support    ---
  Forest                                                               

  Autoencoder   **Lead**   **Lead**   ---        ---        Support    ---

  Reasoning     Support    Support    ---        Support    **Lead**   ---
  engine                                                               

  Trust score   **Lead**   Support    ---        ---        **Lead**   ---

  Explanation   Support    ---        ---        ---        **Lead**   ---

  Correction    Support    ---        ---        ---        **Lead**   Support

  Digital Twin  Support    ---        ---        Support    **Lead**   Support

  Maintenance   Support    ---        Support    Support    **Lead**   Support

  Database      ---        ---        ---        ---        **Lead**   ---

  FastAPI       ---        ---        ---        ---        **Lead**   ---

  Frontend      ---        ---        **Lead**   ---        Support    **Lead**

  WebSockets    ---        Support    Support    ---        **Lead**   Support

  Replay        ---        Support    Support    ---        **Lead**   Support

  Cascade       Support    ---        Support    ---        **Lead**   Support

  Validation    **Lead**   **Lead**   Support    Support    Support    ---

  Deployment    Support    Support    Support    Support    **Lead**   Support

  Demo          All        All        All        All        All        All
  -------------------------------------------------------------------------------

------------------------------------------------------------------------

# 43. Parallel Development Strategy

Do NOT wait for one phase to completely finish before starting all other
work.

## Track A --- Data + ML

``` text
Neha + Muskan + Manan
```

Flow:

``` text
Data
↓
Validation
↓
EDA
↓
Fault Injection
↓
Features
↓
Baseline
↓
ML
↓
Evaluation
```

## Track B --- Frontend

``` text
Medhvi + Darshita
```

Flow:

``` text
Wireframes
↓
Design System
↓
Static UI
↓
Mock Data
↓
API Integration
↓
WebSocket Integration
↓
Polish
```

## Track C --- Backend

``` text
Mitali
```

Flow:

``` text
API Contract
↓
Database
↓
FastAPI
↓
Mock Inference
↓
Real ML
↓
Reasoning
↓
Digital Twin
↓
WebSocket
↓
Cascade
```

------------------------------------------------------------------------

# 44. Integration Checkpoints

## Checkpoint 1

``` text
DATA → ML
```

A clean reading must produce an ML result.

## Checkpoint 2

``` text
ML → BACKEND
```

FastAPI can call ML.

## Checkpoint 3

``` text
BACKEND → DATABASE
```

Anomaly is persisted.

## Checkpoint 4

``` text
BACKEND → FRONTEND
```

Investigation screen displays the actual anomaly.

## Checkpoint 5

``` text
WEBSOCKET → FRONTEND
```

A new anomaly appears without refreshing.

## Checkpoint 6

``` text
ANOMALY → DIGITAL TWIN
```

Sensor health changes.

## Checkpoint 7

``` text
ANOMALY → CASCADE
```

Impact is calculated.

## Checkpoint 8

``` text
FULL SYSTEM → DEMO
```

One scenario works from start to finish.

------------------------------------------------------------------------

# 45. Frontend-Backend Mock Strategy

Frontend development should not wait for the ML model.

Create:

``` text
frontend/src/mock/
```

Example:

``` json
{
  "station_id": "AWS-104",
  "temperature": 55,
  "pressure": 1004,
  "humidity": 48,
  "trust_score": 18,
  "decision": "SENSOR_FAULT"
}
```

The frontend first works with mock responses.

Then replace:

``` text
mockService
```

with:

``` text
apiService
```

without changing the UI components.

------------------------------------------------------------------------

# 46. Critical Data Flow Contract

A reading entering SkyGuard should follow:

``` json
{
  "station_id": "AWS-104",
  "timestamp": "2026-09-04T12:00:00",
  "temperature": 55.0,
  "pressure": 1004.1,
  "humidity": 48.2
}
```

After processing:

``` json
{
  "station_id": "AWS-104",
  "decision": "SENSOR_FAULT",
  "fault_type": "SPIKE",
  "confidence": 0.97,
  "trust_score": 18,
  "suggested_value": 31.8,
  "evidence": [
    "large_temporal_deviation",
    "low_cross_station_agreement",
    "low_cross_sensor_agreement",
    "high_ml_anomaly"
  ]
}
```

The exact internal implementation may evolve, but the contract between
modules must remain stable.

------------------------------------------------------------------------

# 47. Definition of Done

A feature is complete only when:

``` text
Code written
    ↓
Local test
    ↓
Unit/integration test
    ↓
Documentation
    ↓
PR
    ↓
Code review
    ↓
Merged
    ↓
Integrated
    ↓
Demo tested
```

"Code works on my laptop" is not the definition of Done.

------------------------------------------------------------------------

# 48. Final Project Acceptance Checklist

## Repository

-   [ ] GitHub repository
-   [ ] branches
-   [ ] README
-   [ ] documentation
-   [ ] `.env.example`

## Data

-   [ ] real historical data
-   [ ] 10--20 stations target
-   [ ] 3--6 months target
-   [ ] hourly observations
-   [ ] T/P/H
-   [ ] data dictionary
-   [ ] validation
-   [ ] EDA

## Synthetic Data

-   [ ] 500--2,000 events target
-   [ ] spike
-   [ ] drift
-   [ ] frozen
-   [ ] dropout
-   [ ] jump
-   [ ] multivariate
-   [ ] cross-station
-   [ ] ground truth

## ML

-   [ ] statistical baseline
-   [ ] Isolation Forest
-   [ ] Autoencoder
-   [ ] hybrid detector
-   [ ] model artifacts
-   [ ] evaluation

## Reasoning

-   [ ] temporal consistency
-   [ ] cross-sensor consistency
-   [ ] cross-station consistency
-   [ ] persistence
-   [ ] Weather-vs-Sensor decision
-   [ ] fault classifier
-   [ ] trust score
-   [ ] explanation

## Correction

-   [ ] suggested value
-   [ ] confidence
-   [ ] human approval
-   [ ] raw data preserved
-   [ ] audit log

## Digital Twin

-   [ ] health score
-   [ ] trend
-   [ ] fault history
-   [ ] maintenance priority

## Backend

-   [ ] FastAPI
-   [ ] PostgreSQL/Supabase
-   [ ] REST API
-   [ ] WebSockets
-   [ ] replay

## Frontend

-   [ ] Command Center
-   [ ] map
-   [ ] Investigation
-   [ ] Digital Twin
-   [ ] Maintenance
-   [ ] Cascade
-   [ ] live states

## Validation

-   [ ] Precision
-   [ ] Recall
-   [ ] F1
-   [ ] false alarm rate
-   [ ] detection latency
-   [ ] correction MAE
-   [ ] correction RMSE
-   [ ] degradation warning time
-   [ ] cascade cases

## Deployment

-   [ ] Docker
-   [ ] clean-machine test
-   [ ] deterministic demo
-   [ ] backup demo
-   [ ] final rehearsal

------------------------------------------------------------------------

# 49. Final Phase Flow --- One Page Version

``` text
PHASE 0
GIT + SCOPE
        ↓
PHASE 1
DATA COLLECTION
        ↓
PHASE 2
DATA VALIDATION + EDA
        ↓
PHASE 3
FAULT INJECTION
        ↓
PHASE 4
FEATURE ENGINEERING
        ↓
PHASE 5
STATISTICAL BASELINE
        ↓
PHASE 6
ISOLATION FOREST
        ↓
PHASE 7
AUTOENCODER
        ↓
PHASE 8
HYBRID ML DETECTOR
        ↓
PHASE 9
CONSISTENCY ENGINE
        ↓
PHASE 10
WEATHER-vs-SENSOR ENGINE
        ↓
PHASE 11
FAULT CLASSIFICATION
        ↓
PHASE 12
TRUST SCORE + EXPLANATION
        ↓
PHASE 13
SUGGESTED CORRECTION
        ↓
PHASE 14
HUMAN APPROVAL
        ↓
PHASE 15
DIGITAL TWIN
        ↓
PHASE 16
PREDICTIVE MAINTENANCE
        ↓
PHASE 17
DATABASE
        ↓
PHASE 18
FASTAPI BACKEND
        ↓
PHASE 19
FRONTEND
        ↓
PHASE 20
WEBSOCKETS + REAL-TIME REPLAY
        ↓
PHASE 21
CASCADE IMPACT SIMULATOR
        ↓
PHASE 22
FULL INTEGRATION
        ↓
PHASE 23
VALIDATION
        ↓
PHASE 24
TESTING
        ↓
PHASE 25
DOCKER + DEPLOYMENT
        ↓
PHASE 26
DEMO REHEARSAL
        ↓
        SKYGUARD AI
          READY
```

------------------------------------------------------------------------

# 50. The Core Product Story

The implementation should always preserve this chain:

``` text
DETECT
  ↓
UNDERSTAND
  ↓
DISTINGUISH
  ↓
TRUST
  ↓
EXPLAIN
  ↓
CORRECT
  ↓
TRACK HEALTH
  ↓
PRIORITIZE MAINTENANCE
  ↓
SIMULATE IMPACT
  ↓
PREVENT BAD DECISIONS
```

That is what makes SkyGuard different from a normal anomaly-detection
dashboard.
