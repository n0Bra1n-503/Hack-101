# SkyGuard AI --- Full Implementation & Team Execution Blueprint

> **Project:** SkyGuard AI\
> **SIH PS Code:** SIH26073\
> **Track:** Software\
> **Theme:** Disaster Management\
> **Sponsoring Ministry:** Ministry of Earth Sciences (MoES)\
> **Team size:** 6\
> **Document purpose:** Complete implementation plan, phase breakdown,
> ownership, repository structure, data strategy, ML pipeline, frontend,
> backend, real-time integration, Digital Twin, Cascade Impact
> Simulator, validation, database, testing, deployment, and demo
> execution.

------------------------------------------------------------------------

# 0. HOW TO USE THIS DOCUMENT

This document has two layers:

1.  **SOURCE BLUEPRINT CONTENT** --- the project definition and
    technical decisions already present in the uploaded SkyGuard AI
    blueprint. These sections preserve the original terminology,
    features, architecture, dataset strategy, technology
    recommendations, demo script, metrics, limitations, judging
    alignment, and final pitch.
2.  **IMPLEMENTATION EXPANSION** --- a detailed engineering plan added
    on top of the blueprint so that six people can actually build the
    system in parallel without blocking one another.

The implementation expansion is deliberately organized around the six
current team responsibilities:

  -----------------------------------------------------------------------
  Member                  Primary ownership       Secondary ownership
  ----------------------- ----------------------- -----------------------
  Manan                   ML, EDA                 anomaly detection,
                                                  evaluation

  Muskan                  ML, Data Collection     dataset pipeline, fault
                                                  injection, model
                                                  training

  Medhvi                  Frontend, EDA           UI architecture,
                                                  visualization

  Neha                    Data Collection, EDA    data quality,
                                                  preprocessing,
                                                  validation

  Mitali                  Backend, ML, EDA        APIs, database,
                                                  inference integration

  Darshita                Frontend                dashboard
                                                  implementation, UX,
                                                  live states
  -----------------------------------------------------------------------

The most important rule is:

> **Nobody works in an isolated branch forever. Every phase ends with an
> integration checkpoint and a usable artifact.**

------------------------------------------------------------------------

# 1. PROJECT DEFINITION

## 1.1 One-line project definition

SkyGuard AI looks at a weird weather reading and figures out --- like a
detective --- whether the weather is actually doing something unusual,
or whether a sensor has gone faulty. Then it explains its reasoning in
plain words, suggests a safer number to use instead, keeps score of how
healthy every sensor is over time, and tells the maintenance team
exactly which sensor to fix first.

The differentiator is that SkyGuard does not stop at "this number looks
wrong." It aims to answer:

-   Is this actual extreme weather or sensor failure?
-   Why did the system make that decision?
-   How trustworthy is the current reading?
-   What value could safely be used instead?
-   How has the sensor's health changed over time?
-   Which sensor should a maintenance team inspect first?
-   What downstream disaster-management decision could have been
    affected if the bad value had not been caught?

The final question is the **Cascade Impact Simulator X-Factor**.

------------------------------------------------------------------------

# 2. PROBLEM STATEMENT

Weather stations distributed across India report temperature, air
pressure, and humidity continuously. Stations are exposed to sun, rain,
dust, corrosion, calibration drift, electrical problems, and
connectivity failures.

A strange reading therefore has two possible meanings:

1.  **The weather is genuinely unusual.**
2.  **The sensor is producing a faulty value.**

A simple threshold system cannot reliably distinguish these cases.

For example:

-   A sudden temperature spike may be a real heatwave.
-   A pressure crash may be a genuine approaching storm.
-   A single station reporting 55°C while nearby stations remain normal
    may indicate a faulty temperature sensor.
-   A sensor stuck at the same value for hours may indicate a frozen or
    disconnected instrument.

SkyGuard is designed to combine:

-   statistical checks,
-   machine-learning anomaly detection,
-   temporal evidence,
-   cross-sensor evidence,
-   cross-station evidence,
-   persistence,
-   fault classification,
-   trust scoring,
-   explainability,
-   correction suggestions,
-   sensor health history,
-   maintenance prioritization,
-   and downstream cascade simulation.

------------------------------------------------------------------------

# 3. STAKEHOLDERS

## 3.1 MoES / IMD data analyst

Current pain:

-   Hundreds of station feeds.
-   Manual inspection.
-   Fixed thresholds.
-   Alert fatigue.

SkyGuard output:

-   Ranked anomalies.
-   Evidence-backed explanation.
-   Trust score.
-   Fault classification.
-   Suggested correction.

## 3.2 Disaster-management teams

Current pain:

-   A flood, cyclone, or heatwave alert can be affected by incorrect
    input data.

SkyGuard output:

-   A confidence/trust layer around the readings feeding downstream
    decisions.

## 3.3 Field maintenance engineers

Current pain:

-   Fixed schedules may not reflect actual sensor health.

SkyGuard output:

-   Ranked repair queue.
-   Sensor health trend.
-   Reason for priority.
-   Recent fault history.

## 3.4 Farmers / agri-advisory systems

Current pain:

-   Advisories depend on station data.

SkyGuard output:

-   Indirect protection through detection and quarantine of suspicious
    readings before they propagate.

## 3.5 Pilots / aviation meteorological officers

Current pain:

-   Need confidence in weather observations.

SkyGuard output:

-   Confidence-scored observations instead of blind trust in a single
    number.

------------------------------------------------------------------------

# 4. CORE FEATURES --- FINAL PRODUCT CONTRACT

These six features form one connected system, not six separate modules.

## Feature 1 --- Smart Anomaly Detection

Combine:

-   simple rule checks,
-   statistical methods,
-   ML methods.

Target fault types:

-   sudden spike,
-   slow drift,
-   frozen / flatline,
-   dropout / missing data,
-   abrupt jump,
-   multivariate inconsistency.

## Feature 2 --- Weather-vs-Sensor Engine

For every suspicious reading, ask:

### Temporal evidence

Did this sensor change in a physically/plausibly consistent way?

### Cross-sensor evidence

Did temperature, pressure, and humidity move together in a way that
supports the event?

### Cross-station evidence

Did geographically close stations observe something similar?

### Persistence evidence

Did the event persist long enough to look like a genuine weather event?

Then classify the event as:

-   probable genuine weather,
-   probable sensor fault,
-   uncertain / requires review.

## Feature 3 --- AWS Trust Score: 0--100

A simple number representing how much the system currently trusts a
reading.

Example:

``` text
Trust Score: 18/100
Decision: PROBABLE SENSOR FAULT
Fault: Temperature spike
Confidence: 97%
```

The score must be explainable.

Example evidence decomposition:

``` text
Temporal consistency       + 10
Cross-sensor agreement     +  5
Cross-station agreement    +  0
ML anomaly confidence      - 45
Persistence                 - 20
Historical sensor health    - 12
------------------------------------------------
Final trust score             18
```

The exact mathematical weighting must be tuned using validation data. Do
not pretend the initial weights are scientifically established.

## Feature 4 --- Sensor Digital Twin

Every physical/logical sensor gets a continuously updated health
profile.

The Digital Twin should show:

-   station ID,
-   sensor type,
-   current value,
-   trust score,
-   health score,
-   historical anomaly count,
-   recent fault types,
-   last suspicious event,
-   degradation trend,
-   current maintenance priority,
-   last known good value,
-   suggested next action.

Think of it as:

> "A health record for the sensor."

## Feature 5 --- Explainable Correction --- Human Approved

Never silently overwrite the original value.

Pipeline:

``` text
Raw reading
    ↓
Suspicion detected
    ↓
Alternative estimate generated
    ↓
Evidence displayed
    ↓
Human chooses:
    ACCEPT
    REJECT
    REVIEW
    ↓
Raw value remains preserved forever
```

Store:

-   raw value,
-   suggested value,
-   correction method,
-   confidence,
-   reason,
-   reviewer decision,
-   timestamp.

## Feature 6 --- Predictive Maintenance Queue

Turn sensor health into an actionable queue.

Example:

``` text
#1 AWS-104 — HIGH PRIORITY
Reason:
- 7 anomalies in 72 hours
- trust score falling
- repeated temperature spikes
- 3-week degradation trend

#2 AWS-117 — MEDIUM
Reason:
- intermittent dropout
- increasing missingness
```

------------------------------------------------------------------------

# 5. X-FACTOR --- CASCADE IMPACT SIMULATOR

The Cascade Impact Simulator answers:

> "What would have happened if we had not caught this bad reading?"

Example:

``` text
Observed:
AWS-104 temperature = 55°C

SkyGuard:
PROBABLE SENSOR FAULT
Trust = 18/100

Without SkyGuard:
District average would cross illustrative heatwave threshold.

Potential downstream result:
FALSE HEATWAVE ALERT

With SkyGuard:
Suspicious value quarantined.
Suggested safe value = 31.8°C.
Illustrative heatwave rule does not trigger.
```

A second scenario demonstrates the opposite:

``` text
Several nearby stations:
42°C
43°C
41.5°C
42.7°C

Cross-station agreement: HIGH
Cross-sensor agreement: HIGH

SkyGuard:
GENUINE WEATHER EVENT

If suppressed:
Potential delay to a genuine warning.
```

## Important honesty requirement

The Cascade Impact Simulator is an illustrative downstream model.

It is **not** the real IMD forecasting model.

The UI should explicitly label this:

> "Illustrative downstream impact simulation --- not an IMD forecasting
> model."

This is a strength, not a weakness, because it prevents overclaiming.

------------------------------------------------------------------------

# 6. SOURCE BLUEPRINT --- PRESERVED CONTENT

## 6.1 The Idea in One Sentence

SkyGuard AI looks at a weird weather reading and figures out --- like a
detective --- whether the weather is actually doing something unusual,
or whether a sensor has gone faulty. Then it explains its reasoning in
plain words, suggests a safer number to use instead, keeps score of how
healthy every sensor is over time, and tells the maintenance team
exactly which sensor to fix first.

Most competing teams will build something that says "this number looks
wrong." SkyGuard says "this number looks wrong, here's why, here's what
it probably should be, here's how sick this sensor has been getting for
the last 3 weeks, and here's what would have happened downstream if we
hadn't caught it."

That last part is our X-Factor.

## 6.2 The Problem, Explained Simply

Weather stations spread across India constantly report temperature, air
pressure, and humidity --- completely unmanned, 24/7. Like any machine
left outside in the sun, rain, and dust for years, their sensors slowly
go bad: a wire corrodes, a chip drifts out of calibration, a connection
drops. When that happens, the station starts sending wrong numbers ---
but it doesn't know it's wrong, and neither does anyone else, until a
forecast or a flood warning based on that bad number turns out to be
wrong too.

The tricky part is that a weird number isn't always a broken sensor. A
sudden temperature spike could be a real heatwave. A pressure crash
could be a real approaching storm. The system has to be smart enough to
tell these two situations apart --- and today's basic "alert if the
number crosses a fixed limit" systems simply can't.

## 6.3 Empathy Canvas

Persona:

> Priya, a Data Quality Analyst at a State IMD Regional Centre.

Says:

> "I've got 200 station feeds and a spreadsheet of fixed thresholds ---
> I can't tell which alerts are real."

Thinks:

> "Half these alerts are probably nothing. But if I ignore the wrong
> one, someone gets a bad flood warning."

Does:

-   Manually checks flagged outliers.
-   Waits for a field visit report or public complaint to confirm a
    fault.

Feels:

-   Alert fatigue.
-   Quiet anxiety.
-   Worry about missing the one reading that actually mattered.

Before → After:

> "I find out a reading was garbage after a bad forecast already went
> out"

becomes:

> "I get a ranked alert within seconds: 'AWS-104 temperature --- 97%
> likely sensor spike, here's the evidence, here's the safe value to use
> instead, and here's how this sensor's health has been trending for the
> last month.'"

------------------------------------------------------------------------

# 7. END-TO-END SYSTEM ARCHITECTURE

The original blueprint architecture is:

``` text
AWS Sensor Data (real / historical / simulated)
        ↓
Data Ingestion + Validation
(catch missing values, bad timestamps, impossible numbers)
        ↓
Feature Engineering
(rolling averages, rate-of-change, time-of-day/season patterns)
        ↓
+-------------------------------+
| Statistical | ML Detectors    |
| Rules / EWMA | Isolation Forest|
|             | + Autoencoder   |
+-------------------------------+
        ↓
Consistency Engine
(Temporal + Cross-Sensor + Cross-Station + Persistence checks)
        ↓
WEATHER-vs-SENSOR DECISION ENGINE
        ↓
Fault Classifier
(spike / drift / frozen / dropout / multivariate)
        ↓
Trust Score + Explainability + Suggested Correction
(human-approved)
        ↓
Sensor Digital Twin
        ↓
Predictive Maintenance Queue
        ↓
Live Dashboard
(Command Center, Map, Investigation View, Maintenance Queue)
```

## 7.1 Expanded implementation architecture

``` text
                  ┌──────────────────────────────┐
                  │ Historical Weather Dataset   │
                  │ IMD / NOAA / public sources  │
                  └──────────────┬───────────────┘
                                 │
                  ┌──────────────▼───────────────┐
                  │ Synthetic Fault Injector     │
                  │ Spike / Drift / Frozen /     │
                  │ Dropout / Jump / Multivariate│
                  └──────────────┬───────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────┐
│                 DATA INGESTION LAYER                   │
│ CSV / replay / API / optional AWS IoT / simulator      │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│              VALIDATION + NORMALIZATION                │
│ schema / timestamp / range / missingness / duplicates  │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│                 FEATURE ENGINEERING                    │
│ rolling mean/std / delta / rate / lag / time features │
└──────────────────────────┬─────────────────────────────┘
                           ▼
             ┌─────────────┴─────────────┐
             ▼                           ▼
┌──────────────────────┐      ┌──────────────────────────┐
│ Statistical Layer    │      │ ML Layer                 │
│ EWMA / z-score /     │      │ Isolation Forest /       │
│ persistence / rules  │      │ Autoencoder              │
└───────────┬──────────┘      └─────────────┬────────────┘
            └──────────────┬────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│             CONSISTENCY / REASONING ENGINE              │
│ temporal + cross-sensor + cross-station + persistence  │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│             WEATHER-vs-SENSOR DECISION ENGINE          │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ FAULT CLASSIFIER + TRUST SCORE + EXPLANATION           │
└──────────────────────────┬─────────────────────────────┘
                           ▼
             ┌─────────────┴─────────────┐
             ▼                           ▼
┌────────────────────────┐   ┌───────────────────────────┐
│ Suggested Correction   │   │ Digital Twin / Health     │
│ Human approval         │   │ History / Maintenance     │
└────────────┬───────────┘   └─────────────┬─────────────┘
             └──────────────┬──────────────┘
                            ▼
                 ┌────────────────────┐
                 │ Cascade Simulator  │
                 │ before / after     │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │ FastAPI Backend    │
                 │ REST + WebSockets  │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │ React Dashboard    │
                 │ Command Center     │
                 │ Map / Investigation│
                 │ Digital Twin       │
                 │ Maintenance Queue  │
                 │ Cascade View       │
                 └────────────────────┘
```

------------------------------------------------------------------------

# 8. REPOSITORY FIRST --- PHASE 0

## 8.1 GitHub repository

Recommended repository:

``` text
skyguard-ai/
```

## 8.2 Branch strategy

``` text
main
develop
feature/ml-anomaly
feature/data-pipeline
feature/frontend-dashboard
feature/backend-api
feature/digital-twin
feature/cascade-simulator
feature/validation
```

Do not allow direct pushes to `main`.

Recommended flow:

``` text
feature branch
      ↓
pull request
      ↓
review by at least one teammate
      ↓
merge into develop
      ↓
integration test
      ↓
release candidate
      ↓
main
```

## 8.3 Folder structure

``` text
skyguard-ai/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
│
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── data-dictionary.md
│   ├── ml-design.md
│   ├── ui-design.md
│   ├── validation-plan.md
│   └── demo-script.md
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   ├── synthetic/
│   └── README.md
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_eda_temperature.ipynb
│   ├── 03_eda_pressure.ipynb
│   ├── 04_eda_humidity.ipynb
│   ├── 05_fault_injection.ipynb
│   └── 06_model_evaluation.ipynb
│
├── ml/
│   ├── preprocessing/
│   ├── features/
│   ├── detectors/
│   ├── classifiers/
│   ├── scoring/
│   ├── correction/
│   ├── evaluation/
│   └── artifacts/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── websocket/
│   │   ├── database/
│   │   └── core/
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
├── simulator/
│   ├── replay_engine/
│   ├── fault_injector/
│   └── cascade/
│
└── deployment/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── nginx/
```

## 8.4 Git issue labels

Use:

``` text
ML
DATA
EDA
BACKEND
FRONTEND
DATABASE
REALTIME
DIGITAL-TWIN
CASCADE
VALIDATION
BUG
BLOCKER
DOCUMENTATION
DEMO
```

## 8.5 Definition of Done

A task is not complete merely because code runs.

A task is Done when:

-   code is committed,
-   branch is pushed,
-   tests or validation exist,
-   output format is documented,
-   teammate can run it,
-   PR is reviewed,
-   integration assumptions are documented.

------------------------------------------------------------------------

# 9. DATA STRATEGY --- PHASE 1

The original blueprint recommends a two-layer strategy.

## Layer 1 --- Real historical data

Use public IMD/NOAA weather station records.

Target:

-   at least 10--20 stations,
-   3--6 months,
-   hourly data,
-   Temperature,
-   Pressure,
-   Humidity.

A single station is sufficient for a bare MVP, but the target for a
strong demo should be multiple geographically distributed stations.

## Layer 2 --- Synthetic fault injection

Create controlled broken-sensor examples by injecting:

-   spikes,
-   slow drift,
-   frozen values,
-   dropouts,
-   abrupt jumps,
-   cross-sensor inconsistencies.

Each injected fault must have exact ground truth.

## Volume target

The source blueprint gives:

> 500--2,000 synthetic fault events spread across all fault types.

For the implementation, target the upper end if computationally
feasible.

A practical dataset target:

``` text
10–20 stations
3–6 months
hourly observations
3 core variables
+
500–2,000 labeled fault events
```

Do not artificially inflate the number of rows simply to claim "big
data." What matters is diversity, quality, station separation, time
separation, and controlled ground truth.

------------------------------------------------------------------------

# 10. DATA COLLECTION WORKFLOW

## Step 1 --- Define data contract

Every record should eventually map to:

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

Optional metadata:

``` text
station_name
region
elevation
timezone
```

Do not make optional variables mandatory for the core ML model.

The source blueprint explicitly keeps the core model around:

-   Temperature
-   Pressure
-   Humidity

plus calculated features.

## Step 2 --- Acquire raw data

Never edit raw files.

Store them as:

``` text
data/raw/source_name/
```

## Step 3 --- Build ingestion script

Example:

``` text
scripts/download_data.py
scripts/normalize_data.py
scripts/validate_data.py
```

## Step 4 --- Create a data dictionary

Example:

  Field          Type       Meaning
  -------------- ---------- --------------------
  station_id     string     Unique station
  timestamp      datetime   Observation time
  temperature    float      Temperature
  pressure       float      Air pressure
  humidity       float      Relative humidity
  latitude       float      Station latitude
  longitude      float      Station longitude
  source         string     Dataset source
  quality_flag   string     Data-quality state

## Step 5 --- Data quality checks

Check:

-   missing values,
-   duplicate timestamps,
-   duplicate station records,
-   timezone consistency,
-   impossible values,
-   timestamp gaps,
-   station coverage,
-   variable distributions,
-   extreme outliers,
-   flatlines.

------------------------------------------------------------------------

# 11. EDA PLAN

EDA is shared primarily by Manan, Medhvi, Neha, and Mitali.

## 11.1 EDA objectives

EDA must answer:

1.  What does normal weather look like?
2.  How do temperature, pressure, and humidity behave over time?
3.  What are normal daily patterns?
4.  How variable are stations?
5.  How correlated are sensors?
6.  How close do neighboring stations behave?
7.  What types of artificial faults look realistic?
8.  Which features are useful for detection?
9.  Where does missing data occur?
10. How will train/test leakage be prevented?

## 11.2 Required plots

### Time-series

-   temperature vs time,
-   pressure vs time,
-   humidity vs time.

### Distribution

-   histogram,
-   boxplot,
-   percentile range.

### Relationship

-   temperature vs humidity,
-   pressure vs temperature,
-   pressure vs humidity.

### Temporal

-   hourly averages,
-   day-of-week patterns,
-   monthly/seasonal patterns where enough data exists.

### Station comparison

-   station-wise mean,
-   station-wise variance,
-   station-wise missingness,
-   station correlation matrix.

### Fault visualization

For every synthetic fault type, show:

``` text
clean signal
fault-injected signal
ground-truth fault interval
```

This is extremely useful for both ML and frontend demonstrations.

------------------------------------------------------------------------

# 12. FAULT INJECTION LAB

The fault injector is a major shared component between data and ML.

## 12.1 Spike fault

Example:

``` text
Normal:
31.2°C

Injected:
55.0°C

Duration:
1 sample
```

Parameters:

-   magnitude,
-   duration,
-   direction,
-   station,
-   variable.

## 12.2 Slow drift

Example:

``` text
31.0
31.2
31.4
31.7
32.0
32.5
33.0
...
```

The point is that the value may not violate an absolute threshold
immediately.

## 12.3 Frozen / flatline

Example:

``` text
31.8
31.8
31.8
31.8
31.8
31.8
```

Duration must vary.

## 12.4 Dropout

Replace readings with:

``` text
NaN
```

or mark them as missing according to the chosen pipeline.

## 12.5 Abrupt jump

A step change that persists:

``` text
31 → 32 → 33 → 42 → 42 → 42
```

## 12.6 Cross-sensor inconsistency

Example:

``` text
Temperature rises sharply
Humidity and pressure remain completely unchanged
```

The point is not to declare this automatically faulty; it is evidence
for the reasoning engine.

## 12.7 Cross-station inconsistency

One station spikes while geographically close stations remain normal.

Again, this is evidence, not absolute proof.

## 12.8 Ground-truth schema

Every injected event must have:

``` text
event_id
station_id
variable
fault_type
start_timestamp
end_timestamp
original_value
corrupted_value
injection_parameters
severity
ground_truth
```

------------------------------------------------------------------------

# 13. TRAIN / VALIDATION / TEST SPLIT

Do not randomly split individual rows only.

That can leak nearly identical neighboring timestamps into training and
testing.

Preferred strategy:

## Split by time and/or station

Example:

``` text
Training:
Stations A–L
January–April

Validation:
Stations A–L
May

Test:
Held-out stations M–P
June
```

The exact arrangement depends on the available data.

The principle is:

> The model must prove that it generalizes to unseen time periods and
> preferably unseen stations.

------------------------------------------------------------------------

# 14. FEATURE ENGINEERING

Core variables:

``` text
temperature
pressure
humidity
```

Derived features:

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

## Temporal features

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
temperature_humidity_relation
temperature_change_vs_humidity_change
pressure_change_vs_temperature_change
```

## Cross-station features

``` text
neighbor_mean
neighbor_median
neighbor_std
difference_from_neighbor_mean
```

These must be calculated carefully to avoid using future information.

------------------------------------------------------------------------

# 15. ML ARCHITECTURE

The source blueprint recommends:

-   Isolation Forest,
-   Autoencoder.

The ML team should build in this order:

``` text
Baseline rules
    ↓
Statistical detector
    ↓
Isolation Forest
    ↓
Autoencoder
    ↓
Hybrid ensemble
    ↓
Weather-vs-Sensor reasoning
```

Do not begin with the deep-learning model.

------------------------------------------------------------------------

# 16. BASELINE DETECTORS

## 16.1 Why baseline first?

If ML fails, the project should still have a working detector.

Baseline methods provide:

-   explainability,
-   comparison,
-   sanity checks,
-   debugging signals.

## 16.2 Baseline examples

### Range rules

Only as a validation/safety layer, not the whole system.

### Z-score

``` text
z = (x - mean) / standard_deviation
```

### Rolling z-score

Compare a reading with recent local behavior.

### EWMA

Exponentially weighted moving average for detecting changes in a time
series.

### Persistence rule

Repeated suspicious readings can increase confidence.

------------------------------------------------------------------------

# 17. ISOLATION FOREST

Purpose:

Detect unusual feature combinations without requiring every fault type
to be labeled.

Input features may include:

``` text
temperature
pressure
humidity
delta_1
delta_3
rolling_mean
rolling_std
neighbor_difference
```

Output:

``` text
anomaly_score
is_anomaly
```

The team should calibrate the threshold on validation data rather than
blindly using a default.

------------------------------------------------------------------------

# 18. AUTOENCODER

Train primarily on clean/normal data.

Concept:

``` text
normal input
   ↓
encoder
   ↓
compressed representation
   ↓
decoder
   ↓
reconstruction
```

For normal patterns:

``` text
reconstruction error = low
```

For unusual patterns:

``` text
reconstruction error = high
```

Output:

``` text
reconstruction_error
anomaly_probability_or_score
```

The score must be calibrated before being presented as "confidence."

------------------------------------------------------------------------

# 19. HYBRID DETECTION

Do not let one model decide everything.

Example conceptual ensemble:

``` text
Rule evidence
      +
Statistical evidence
      +
Isolation Forest evidence
      +
Autoencoder evidence
      +
Temporal consistency
      +
Cross-sensor consistency
      +
Cross-station consistency
      +
Persistence
      ↓
Decision engine
```

A first implementation can use a weighted evidence score.

Later, if validation supports it, the weighting can be learned.

------------------------------------------------------------------------

# 20. WEATHER-vs-SENSOR DECISION ENGINE

This is the core intelligence layer.

## Input

``` text
current reading
historical context
other sensor readings
neighbor stations
ML scores
statistical scores
sensor health
```

## Output

``` json
{
  "decision": "SENSOR_FAULT",
  "fault_type": "SPIKE",
  "confidence": 0.97,
  "trust_score": 18,
  "suggested_value": 31.8,
  "reason_codes": [
    "single_station_deviation",
    "cross_sensor_mismatch",
    "high_ml_anomaly",
    "short_duration"
  ]
}
```

## Example evidence chain

``` text
Temperature jumped from 31.2°C to 55.0°C.
Nearby stations remained between 30.8°C and 32.1°C.
Humidity and pressure did not show corresponding changes.
Isolation Forest marked the observation anomalous.
The autoencoder reconstruction error is high.
The sensor has previously shown increasing anomalies.

Decision:
Probable sensor spike.

Confidence:
97%.

Trust:
18/100.
```

The explanation should be generated from structured evidence, not
invented by a language model.

------------------------------------------------------------------------

# 21. TRUST SCORE DESIGN

The trust score is 0--100.

Interpretation:

``` text
90–100  Very high trust
75–89   High trust
50–74   Moderate / monitor
25–49   Low trust
0–24    Very low trust
```

This is a product-level interpretation and should be calibrated against
validation results.

Possible components:

``` text
Temporal consistency
Cross-sensor agreement
Cross-station agreement
ML anomaly evidence
Historical sensor health
Missingness
Persistence
```

Keep the raw component scores in the database.

That makes the trust score explainable.

------------------------------------------------------------------------

# 22. SUGGESTED CORRECTION ENGINE

The system proposes a value; it does not silently modify reality.

Possible correction strategies:

1.  Neighbor-station median.
2.  Local rolling estimate.
3.  Cross-sensor regression.
4.  Interpolation for short gaps.
5.  Model-based reconstruction.

The method selected must depend on fault type.

Example:

``` text
Spike:
use local + neighbor estimate

Dropout:
interpolate or estimate from neighboring observations

Frozen:
estimate from recent trend and nearby stations

Cross-station inconsistency:
neighbor median may be useful
```

Every correction must include:

``` text
correction_method
suggested_value
confidence
supporting_evidence
```

------------------------------------------------------------------------

# 23. DIGITAL TWIN

## 23.1 Digital Twin object

Example:

``` json
{
  "station_id": "AWS-104",
  "sensor_type": "temperature",
  "health_score": 62,
  "trust_score": 18,
  "status": "DEGRAADING",
  "fault_count_7d": 4,
  "fault_count_30d": 11,
  "last_fault_type": "SPIKE",
  "last_fault_at": "2026-...",
  "trend": "DECLINING",
  "maintenance_priority": "HIGH"
}
```

## 23.2 Health score

Health should not simply equal trust.

Trust is:

> "How much do I trust this reading right now?"

Health is:

> "How healthy does this sensor appear over time?"

This distinction is important.

------------------------------------------------------------------------

# 24. PREDICTIVE MAINTENANCE

Rank sensors using:

``` text
current trust
health trend
fault frequency
fault severity
recency
persistence
duration
data availability
```

Example priority score:

``` text
priority =
  0.35 * degradation
+ 0.25 * recent_fault_rate
+ 0.20 * trust_risk
+ 0.20 * severity
```

The exact weights should be validated rather than presented as
scientifically universal.

Output:

``` text
Sensor
Priority
Health
Trend
Fault count
Reason
Recommended action
```

------------------------------------------------------------------------

# 25. DATABASE DESIGN

Recommended database:

> PostgreSQL / Supabase

## Core tables

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
serial_or_logical_id
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

# 26. BACKEND --- FASTAPI

Backend responsibilities:

-   receive readings,
-   validate readings,
-   invoke ML inference,
-   run reasoning engine,
-   calculate trust,
-   generate correction suggestion,
-   update Digital Twin,
-   update maintenance queue,
-   run Cascade Simulator,
-   persist results,
-   stream events to frontend.

## Suggested API

``` text
GET    /api/stations
GET    /api/stations/{station_id}
GET    /api/stations/{station_id}/readings
GET    /api/stations/{station_id}/health
GET    /api/stations/{station_id}/anomalies

POST   /api/readings
POST   /api/inference
POST   /api/corrections/{id}/accept
POST   /api/corrections/{id}/reject
POST   /api/corrections/{id}/review

GET    /api/anomalies
GET    /api/anomalies/{id}

GET    /api/maintenance
GET    /api/cascade/{anomaly_id}

POST   /api/simulator/inject
POST   /api/replay/start
POST   /api/replay/stop

WS     /ws/live
```

------------------------------------------------------------------------

# 27. API RESPONSE CONTRACT

A live anomaly response should contain everything the frontend needs.

Example:

``` json
{
  "event_id": "evt-001",
  "station_id": "AWS-104",
  "timestamp": "2026-09-04T12:00:00",
  "variable": "temperature",
  "value": 55.0,
  "decision": "SENSOR_FAULT",
  "fault_type": "SPIKE",
  "confidence": 0.97,
  "trust_score": 18,
  "suggested_value": 31.8,
  "explanation": [
    "Large deviation from recent station history",
    "Nearby stations remained normal",
    "Cross-sensor behavior does not support the spike",
    "ML detectors marked the observation anomalous"
  ],
  "digital_twin": {
    "health_score": 62,
    "trend": "DECLINING"
  },
  "cascade": {
    "without_skyguard": "ILLUSTRATIVE_FALSE_HEATWAVE",
    "with_skyguard": "NO_ALERT"
  }
}
```

------------------------------------------------------------------------

# 28. REAL-TIME INTEGRATION

The source blueprint recommends WebSockets for live/replay event
streaming.

The project should support two modes.

## Mode A --- Replay mode

Historical/synthetic data is replayed at accelerated speed.

Example:

``` text
1 historical hour
→ replayed every 2 seconds
```

This is the primary hackathon demo mode.

## Mode B --- Live ingestion

Optional extension:

``` text
AWS IoT / MQTT / external API
        ↓
ingestion adapter
        ↓
FastAPI
        ↓
ML pipeline
        ↓
WebSocket
        ↓
dashboard
```

The architecture should keep the ingestion interface generic so the
model does not care whether the source is CSV replay, API, simulator, or
live feed.

## Important honesty statement

For the final demo, if the system uses replay:

> "Real-time demonstration uses a timed replay of historical/synthetic
> data; it is not a production live AWS feed."

This is explicitly called out as an honest limitation in the source
blueprint.

------------------------------------------------------------------------

# 29. FRONTEND PRODUCT DESIGN

The frontend should look like an operational command center, not a
generic student dashboard.

## Visual direction

Use:

-   dark operational dashboard,
-   high information density,
-   restrained accent colors,
-   clear green / amber / red status states,
-   large trust score,
-   map,
-   time-series charts,
-   anomaly feed,
-   Digital Twin,
-   maintenance queue,
-   Cascade impact panel.

Recommended stack:

-   React,
-   Vite,
-   Tailwind CSS,
-   Recharts or Plotly,
-   Leaflet.

## Main navigation

``` text
Command Center
Stations Map
Investigation
Sensor Digital Twins
Maintenance Queue
Cascade Simulator
System / Data Health
```

------------------------------------------------------------------------

# 30. COMMAND CENTER

This is the first screen judges should see.

Top summary cards:

``` text
TOTAL STATIONS
HEALTHY
DEGRADING
CRITICAL
ACTIVE ANOMALIES
AVG TRUST
```

Main sections:

### Network map

Station markers:

-   green = healthy,
-   amber = suspicious,
-   red = critical.

### Live anomaly feed

Example:

``` text
12:03:14
AWS-104
Temperature spike
Trust 18
97% likely fault

12:03:11
AWS-112
Humidity dropout
Trust 42
Review required
```

### Trust distribution

A visual showing the current network health.

### Maintenance preview

Top 5 sensors requiring action.

------------------------------------------------------------------------

# 31. STATION MAP

Each marker opens:

``` text
Station ID
Location
Current T/P/H
Trust
Health
Last anomaly
Status
```

Clicking opens the investigation view.

Use Leaflet.

------------------------------------------------------------------------

# 32. INVESTIGATION VIEW

This is the most important analytical screen.

Layout:

``` text
┌───────────────────────────────────────────┐
│ AWS-104 | Temperature | SENSOR FAULT      │
├──────────────┬────────────────────────────┤
│ Trust 18/100 │ Confidence 97%             │
├──────────────┴────────────────────────────┤
│ Temperature time-series                   │
│                                           │
├───────────────────────────────────────────┤
│ Evidence                                  │
│ ✓ Recent history                          │
│ ✕ Neighbor agreement                      │
│ ✕ Cross-sensor consistency                │
│ ✕ ML normality                            │
├───────────────────────────────────────────┤
│ Suggested correction: 31.8°C              │
│ [ACCEPT] [REJECT] [REVIEW]                │
└───────────────────────────────────────────┘
```

The user should understand the decision in less than 10 seconds.

------------------------------------------------------------------------

# 33. DIGITAL TWIN UI

Show:

``` text
AWS-104

Health:
62/100

Current Trust:
18/100

Trend:
DECLINING

7-day faults:
4

30-day faults:
11

Last fault:
Temperature spike

Maintenance:
HIGH PRIORITY
```

Add a health timeline.

The timeline should make the "sensor is getting sick" narrative visually
obvious.

------------------------------------------------------------------------

# 34. MAINTENANCE QUEUE UI

Columns:

``` text
Priority
Sensor
Health
Trust
Trend
Fault frequency
Last fault
Reason
Action
```

Example:

``` text
#1 AWS-104
Health 62
Trust 18
Declining
11 faults / 30d
Spike
Repeated anomalies + degradation
INSPECT

#2 AWS-117
Health 71
Trust 43
Declining
7 faults / 30d
Dropout
Intermittent connectivity
INSPECT
```

------------------------------------------------------------------------

# 35. CASCADE SIMULATOR UI

This must be visually strong.

Suggested layout:

``` text
             BAD READING
                 ↓
          SkyGuard decision
                 ↓
      ┌──────────┴──────────┐
      │                     │
WITHOUT SKYGUARD       WITH SKYGUARD
      │                     │
55°C enters rule      suspicious value
      │               quarantined
      ↓                     ↓
FALSE ALERT             NO FALSE ALERT
```

Then show:

``` text
Potential impact prevented:
ILLUSTRATIVE FALSE HEATWAVE ALERT
```

For the genuine weather scenario:

``` text
Multiple stations agree
        ↓
SkyGuard keeps event
        ↓
GENUINE EXTREME WEATHER
```

------------------------------------------------------------------------

# 36. FRONTEND STATE MANAGEMENT

The frontend needs at least these states:

``` text
stations
liveReadings
anomalies
selectedStation
selectedAnomaly
maintenanceQueue
digitalTwin
cascadeResult
connectionStatus
loading
error
```

Do not duplicate backend business logic inside React.

Frontend should display backend decisions.

------------------------------------------------------------------------

# 37. REAL-TIME FRONTEND FLOW

``` text
WebSocket connected
        ↓
receive reading event
        ↓
update live station state
        ↓
receive inference event
        ↓
add anomaly
        ↓
update trust
        ↓
update Digital Twin
        ↓
update maintenance queue
        ↓
render notification
```

Connection states:

``` text
LIVE
RECONNECTING
OFFLINE
REPLAY MODE
```

Make this visible.

------------------------------------------------------------------------

# 38. BACKEND SERVICE LAYERS

Recommended separation:

``` text
api/
services/
ml/
database/
websocket/
```

Example services:

``` text
ingestion_service.py
validation_service.py
feature_service.py
inference_service.py
reasoning_service.py
trust_service.py
correction_service.py
digital_twin_service.py
maintenance_service.py
cascade_service.py
replay_service.py
```

This avoids putting the entire application into `main.py`.

------------------------------------------------------------------------

# 39. MLI / BACKEND INTEGRATION CONTRACT

Mitali and the ML team must agree on a stable inference function.

Example:

``` python
result = inference_engine.predict(
    station_id=station_id,
    timestamp=timestamp,
    temperature=temperature,
    pressure=pressure,
    humidity=humidity,
    context=context
)
```

Output:

``` python
{
    "anomaly_score": ...,
    "statistical_score": ...,
    "is_anomaly": ...,
    "fault_type": ...,
    "confidence": ...,
    "trust_score": ...,
    "suggested_value": ...,
    "evidence": [...]
}
```

The exact implementation can evolve, but the contract should remain
stable.

------------------------------------------------------------------------

# 40. PHASE PLAN

## Phase 0 --- Scope Freeze + Git

Owners: - Everyone

Lead: - Mitali

Deliverables:

-   GitHub repository,
-   folder structure,
-   branch strategy,
-   issue board,
-   README,
-   architecture diagram,
-   API contract draft,
-   data contract,
-   MVP definition.

Exit condition:

> Every member can clone the repo and run the basic project skeleton.

------------------------------------------------------------------------

## Phase 1 --- Data Audit + Pipeline

Lead: - Neha

Support: - Muskan, Manan, Mitali

Deliverables:

-   raw dataset,
-   source documentation,
-   data dictionary,
-   ingestion script,
-   validation script,
-   cleaned dataset,
-   EDA notebook.

Exit condition:

> Clean data can be loaded reproducibly with one documented command.

------------------------------------------------------------------------

## Phase 2 --- Fault Injection Lab

Lead: - Muskan

Support: - Neha, Manan

Deliverables:

-   fault generators,
-   reproducibility seed,
-   500--2,000 fault events,
-   labels,
-   visualizations,
-   train/validation/test splits.

Exit condition:

> Given a seed, the same synthetic faults can be reproduced.

------------------------------------------------------------------------

## Phase 3 --- Feature Engineering

Lead: - Manan

Support: - Muskan, Neha, Mitali

Deliverables:

-   feature pipeline,
-   rolling features,
-   change features,
-   temporal features,
-   cross-sensor features,
-   cross-station features.

Exit condition:

> The exact same feature function works in training and inference.

------------------------------------------------------------------------

## Phase 4 --- Statistical Baseline

Lead: - Manan

Support: - Muskan

Deliverables:

-   rule detector,
-   z-score detector,
-   EWMA detector,
-   persistence logic,
-   baseline metrics.

Exit condition:

> There is a measurable baseline before ML.

------------------------------------------------------------------------

## Phase 5 --- ML Models

Lead: - Muskan

Support: - Manan, Mitali

Deliverables:

-   Isolation Forest,
-   Autoencoder,
-   saved model artifacts,
-   inference wrapper,
-   evaluation report.

Exit condition:

> A single input can be passed through both ML models and produce
> standardized outputs.

------------------------------------------------------------------------

## Phase 6 --- Consistency + Weather-vs-Sensor Engine

Lead: - Mitali

Support: - Manan, Muskan, Neha

Deliverables:

-   temporal consistency,
-   cross-sensor consistency,
-   cross-station consistency,
-   persistence,
-   decision engine,
-   evidence codes.

Exit condition:

> The system can distinguish at least the two headline scenarios:
> isolated faulty spike vs coordinated genuine weather event.

------------------------------------------------------------------------

## Phase 7 --- Trust Score + Fault Classifier + Explanation

Lead: - Manan + Mitali

Support: - Muskan

Deliverables:

-   0--100 trust score,
-   fault type,
-   confidence,
-   evidence decomposition,
-   explanation generator.

Exit condition:

> Every anomaly has a structured explanation and score.

------------------------------------------------------------------------

## Phase 8 --- Correction + Digital Twin + Maintenance

Lead: - Mitali

Support: - Manan, Neha

Deliverables:

-   correction engine,
-   human approval,
-   Digital Twin,
-   health history,
-   maintenance queue.

Exit condition:

> A detected fault can flow all the way from anomaly to correction
> suggestion to maintenance priority.

------------------------------------------------------------------------

## Phase 9 --- Backend + Dashboard

Lead: - Mitali for backend, - Medhvi + Darshita for frontend.

Support: - Everyone

Deliverables:

-   FastAPI,
-   PostgreSQL/Supabase,
-   REST APIs,
-   WebSockets,
-   Command Center,
-   Map,
-   Investigation,
-   Digital Twin,
-   Maintenance Queue.

Exit condition:

> The system works end-to-end through the UI.

------------------------------------------------------------------------

## Phase 10 --- Real-Time + Replay Integration

Lead: - Mitali

Support: - Darshita, Medhvi, Muskan

Deliverables:

-   replay engine,
-   WebSocket stream,
-   live anomaly notifications,
-   connection state,
-   optional live adapter.

Exit condition:

> A fault can be injected/replayed and appear on the dashboard in real
> time.

------------------------------------------------------------------------

## Phase 11 --- Cascade Impact Simulator

Lead: - Mitali

Support: - Medhvi, Darshita, Manan

Deliverables:

-   downstream illustrative rule,
-   before/after calculation,
-   Cascade API,
-   Cascade UI,
-   two deterministic scenarios.

Exit condition:

> The demo visibly shows a false alert prevented and a genuine event
> preserved.

------------------------------------------------------------------------

## Phase 12 --- Validation

Lead: - Manan

Support: - Muskan, Neha

Deliverables:

-   precision,
-   recall,
-   F1,
-   false alarm rate during genuine weather,
-   detection latency,
-   correction MAE/RMSE,
-   degradation warning time,
-   cascade cases.

Exit condition:

> Every major claim in the presentation has a measured result or is
> explicitly labeled qualitative.

------------------------------------------------------------------------

## Phase 13 --- Deployment + Rehearsal

Lead: - Everyone

Backend: - Mitali

Frontend: - Medhvi + Darshita

ML: - Manan + Muskan

Data: - Neha

Deliverables:

-   Docker,
-   clean setup,
-   demo dataset,
-   deterministic scenarios,
-   backup video,
-   pitch script,
-   Q&A.

Exit condition:

> The complete system can be started on a clean machine and the full
> demo can be completed without manual debugging.

------------------------------------------------------------------------

# 41. INDIVIDUAL WORK PLAN --- MANAN

## Primary role

**ML + EDA**

## Own these modules

``` text
ml/features/
ml/detectors/
ml/evaluation/
notebooks/01–06
```

## Phase-by-phase

### Phase 0

-   Understand data contract.
-   Define ML input/output contract.
-   Define baseline metrics.

### Phase 1

-   EDA.
-   Analyze distributions.
-   Analyze station behavior.
-   Identify useful feature families.

### Phase 2

-   Help Muskan validate fault injection realism.
-   Analyze whether injected faults are distinguishable.

### Phase 3

Build feature engineering.

Required outputs:

``` text
rolling statistics
rate of change
time features
station-normalized features
cross-sensor features
neighbor features
```

### Phase 4

Build baseline:

``` text
z-score
rolling z-score
EWMA
persistence
```

### Phase 5

Work with Muskan on model evaluation.

### Phase 6

Provide evidence to reasoning engine.

### Phase 7

Own evaluation of:

-   trust-score calibration,
-   confidence calibration,
-   fault-classification quality.

### Phase 12

Own final validation report.

## Manan's Definition of Done

-   notebooks are reproducible,
-   scripts are extracted from notebooks,
-   model results are saved,
-   no training-only code is required for inference,
-   metrics are documented.

------------------------------------------------------------------------

# 42. INDIVIDUAL WORK PLAN --- MUSKAN

## Primary role

**ML + Data Collection**

## Own

``` text
data/raw/
data/processed/
data/synthetic/
ml/detectors/
simulator/fault_injector/
```

## Responsibilities

### Data collection

-   Find and download approved public weather datasets.
-   Document source.
-   Standardize fields.
-   Coordinate station selection.

### Fault injection

Build:

``` text
inject_spike()
inject_drift()
inject_flatline()
inject_dropout()
inject_jump()
inject_multivariate_inconsistency()
```

Each function must be reproducible.

### ML

Train:

-   Isolation Forest,
-   Autoencoder.

Produce:

``` text
model artifact
scaler artifact
feature list
threshold configuration
evaluation report
```

### Integration

Expose one inference wrapper.

## Muskan's Definition of Done

-   model can be loaded without retraining,
-   inference works on one reading/window,
-   synthetic labels are preserved,
-   model artifacts are versioned.

------------------------------------------------------------------------

# 43. INDIVIDUAL WORK PLAN --- MEDHVI

## Primary role

**Frontend + EDA**

## Own

``` text
frontend/src/components/
frontend/src/pages/
frontend/src/layouts/
frontend/src/services/
```

## Responsibilities

### EDA support

-   Decide which charts actually communicate the ML story.
-   Convert analytical findings into visual requirements.

### Frontend architecture

Create reusable:

``` text
StatusCard
TrustScore
StationMap
AnomalyFeed
TimeSeriesChart
EvidencePanel
CorrectionCard
DigitalTwinCard
MaintenanceTable
CascadePanel
ConnectionStatus
```

### Pages

``` text
CommandCenter
StationMap
Investigation
DigitalTwin
Maintenance
Cascade
```

### Design system

Define:

-   typography,
-   spacing,
-   cards,
-   badges,
-   alert states,
-   chart conventions.

## Medhvi's Definition of Done

-   responsive layout,
-   reusable components,
-   loading states,
-   error states,
-   empty states,
-   live state,
-   consistent visual language.

------------------------------------------------------------------------

# 44. INDIVIDUAL WORK PLAN --- NEHA

## Primary role

**Data Collection + EDA**

## Own

``` text
data/
notebooks/01_data_audit.ipynb
notebooks/02–04 EDA
scripts/data_pipeline/
```

## Responsibilities

### Data acquisition

-   station selection,
-   raw file management,
-   source documentation.

### Data quality

Build checks for:

-   nulls,
-   duplicates,
-   invalid timestamps,
-   impossible values,
-   gaps,
-   station metadata.

### EDA

Produce:

-   data-quality report,
-   station coverage report,
-   missingness report,
-   distribution report,
-   correlation analysis.

### ML support

-   communicate normal ranges,
-   help validate fault injection,
-   identify station neighborhoods.

## Neha's Definition of Done

A fresh teammate should be able to understand:

> Where did the data come from, what was changed, what was removed, and
> why?

without asking Neha directly.

------------------------------------------------------------------------

# 45. INDIVIDUAL WORK PLAN --- MITALI

## Primary role

**Backend + ML integration + EDA**

## Own

``` text
backend/
database/
ml/integration/
simulator/replay_engine/
simulator/cascade/
```

## Responsibilities

### Backend architecture

Build FastAPI.

### Database

Build PostgreSQL/Supabase schema.

### API

Implement:

-   readings,
-   stations,
-   anomalies,
-   corrections,
-   health,
-   maintenance,
-   cascade,
-   replay,
-   WebSocket.

### ML integration

Connect model output to API.

### Reasoning engine

Coordinate:

``` text
ML evidence
statistical evidence
cross-sensor evidence
cross-station evidence
historical health
```

### Digital Twin

Build health update service.

### Cascade

Build simulator API.

### EDA

Support feature sanity checking and backend-ready aggregation.

## Mitali's Definition of Done

The backend must run independently and expose a stable contract to the
frontend.

------------------------------------------------------------------------

# 46. INDIVIDUAL WORK PLAN --- DARSHITA

## Primary role

**Frontend**

## Own

``` text
frontend/src/pages/
frontend/src/components/
frontend/src/hooks/
frontend/src/store/
```

## Responsibilities

### Dashboard

Build:

-   Command Center,
-   anomaly feed,
-   station detail,
-   maintenance queue.

### Real-time

Consume WebSocket events.

### User interaction

Implement:

``` text
Accept
Reject
Review
Open investigation
Open Digital Twin
Run Cascade
```

### Demo mode

Add:

``` text
Replay
Inject fault
Pause
Resume
Reset
```

### UX

Make sure judges can understand the story without reading documentation.

## Darshita's Definition of Done

A judge can:

1.  see the network,
2.  see a suspicious station,
3.  open the investigation,
4.  understand why it is suspicious,
5.  see correction,
6.  see Digital Twin,
7.  see maintenance priority,
8.  see cascade impact.

------------------------------------------------------------------------

# 47. WORK DEPENDENCY MATRIX

  Work               Owner               Depends on
  ------------------ ------------------- ---------------------------
  Raw data           Neha/Muskan         Scope
  EDA                Neha/Manan          Raw data
  Fault injection    Muskan              Clean data
  Features           Manan               Clean data
  ML                 Manan/Muskan        Features
  Reasoning engine   Mitali              ML + data context
  Database           Mitali              Data/API contract
  Backend            Mitali              ML contract
  UI design          Medhvi/Darshita     Product contract
  Frontend           Medhvi/Darshita     API contract
  WebSockets         Mitali              Backend
  Live UI            Darshita            WebSocket contract
  Digital Twin       Mitali              Database + anomaly output
  Maintenance        Mitali              Digital Twin
  Cascade            Mitali              anomaly output
  Cascade UI         Medhvi/Darshita     Cascade API
  Validation         Manan/Muskan/Neha   Complete pipeline
  Demo               Everyone            Integrated system

------------------------------------------------------------------------

# 48. PARALLEL WORK STRATEGY

The team should not wait for one person to finish everything.

## Week-style parallelization

### Track A --- Data/ML

Manan + Muskan + Neha

``` text
data
→ EDA
→ faults
→ features
→ baseline
→ ML
```

### Track B --- Product/Frontend

Medhvi + Darshita

``` text
wireframe
→ design system
→ static UI
→ mock JSON
→ API integration
→ WebSocket integration
```

### Track C --- Backend/Integration

Mitali

``` text
API contract
→ database
→ FastAPI
→ mock inference
→ real inference
→ WebSockets
→ Digital Twin
→ Cascade
```

This allows frontend work to continue using mock data while ML is still
being trained.

------------------------------------------------------------------------

# 49. MOCK DATA CONTRACT

Frontend should not wait for ML.

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
  "status": "SENSOR_FAULT"
}
```

When backend becomes available, replace the mock service with API calls
without rebuilding UI components.

------------------------------------------------------------------------

# 50. INTEGRATION CHECKPOINTS

## Checkpoint 1

``` text
Data → ML
```

Input: clean/synthetic record

Output: standardized anomaly result.

## Checkpoint 2

``` text
ML → Backend
```

FastAPI can call inference.

## Checkpoint 3

``` text
Backend → Database
```

Anomaly persists.

## Checkpoint 4

``` text
Backend → Frontend
```

Investigation screen displays real anomaly.

## Checkpoint 5

``` text
WebSocket → Frontend
```

Live event appears.

## Checkpoint 6

``` text
Anomaly → Digital Twin
```

Health changes.

## Checkpoint 7

``` text
Anomaly → Cascade
```

Before/after impact appears.

## Checkpoint 8

``` text
Complete system → Demo
```

All modules run from one command.

------------------------------------------------------------------------

# 51. TESTING STRATEGY

## Unit tests

### Data

-   timestamp parsing,
-   validation,
-   missingness,
-   fault injection.

### ML

-   feature calculation,
-   inference shape,
-   model loading,
-   score ranges.

### Backend

-   API responses,
-   database writes,
-   correction actions,
-   WebSocket messages.

### Frontend

-   components,
-   state changes,
-   API error handling,
-   live updates.

## Integration tests

Test:

``` text
reading
→ validation
→ feature engineering
→ ML
→ reasoning
→ database
→ WebSocket
→ frontend
```

------------------------------------------------------------------------

# 52. VALIDATION PLAN

The source blueprint defines these success metrics:

## Precision / Recall / F1

Measures detection quality.

## False Alarm Rate During Genuine Weather

Critical metric for proving that the Weather-vs-Sensor engine is not
simply an outlier detector.

## Detection Latency

Measure:

``` text
event timestamp
→ system detection timestamp
```

Report:

``` text
mean latency
median latency
p95 latency
```

## Correction Error

Use:

``` text
MAE
RMSE
```

Compare suggested correction with clean ground truth for synthetic
faults.

## Early Degradation Warning Time

Measure how early the Digital Twin identifies degradation before a
severe fault.

## Cascade Impact Cases

Count demonstrated cases where:

-   false alert is prevented,
-   genuine event is preserved.

------------------------------------------------------------------------

# 53. VALIDATION EXPERIMENT MATRIX

Run at least:

### Experiment A --- Spike

Input:

``` text
one station spikes
neighbors normal
```

Expected:

``` text
sensor fault
```

### Experiment B --- Genuine heat event

Input:

``` text
multiple nearby stations spike together
```

Expected:

``` text
genuine weather
```

### Experiment C --- Drift

Expected:

``` text
gradual degradation
```

### Experiment D --- Flatline

Expected:

``` text
frozen sensor
```

### Experiment E --- Dropout

Expected:

``` text
missing-data fault
```

### Experiment F --- Multivariate inconsistency

Expected:

``` text
review/fault depending on evidence
```

------------------------------------------------------------------------

# 54. DEMO SCENARIOS

## Scenario 1 --- The 55°C liar

1.  Open Command Center.
2.  Show healthy network.
3.  Inject 55°C spike at AWS-104.
4.  Keep nearby stations normal.
5.  WebSocket pushes event.
6.  SkyGuard flags it.
7.  Show evidence.
8.  Show 18/100 trust.
9.  Show 97% confidence.
10. Show suggested correction.
11. Trigger Cascade.
12. Show false heatwave alert without SkyGuard.
13. Accept correction.
14. Open Digital Twin.
15. Show degradation.
16. Show maintenance queue priority.

## Scenario 2 --- Real heat event

1.  Reset.
2.  Simultaneously increase temperature across multiple nearby stations.
3.  Keep pressure/humidity behavior consistent enough for the scenario.
4.  Show cross-station agreement.
5.  SkyGuard decides genuine weather.
6.  Trust remains high enough.
7.  Cascade shows that suppressing it could delay a genuine warning.

## Scenario 3 --- Sick sensor

1.  Replay a multi-week degradation sequence.
2.  Show health declining.
3.  Current value may still look plausible.
4.  Digital Twin detects trend.
5.  Maintenance queue raises priority before catastrophic failure.

------------------------------------------------------------------------

# 55. WINNING DEMO SCRIPT --- SOURCE BLUEPRINT PRESERVED

1.  Open the Command Center --- show a healthy network, all stations
    green, high trust scores.
2.  Inject a sudden 55°C temperature spike at one station while
    neighboring stations stay normal.
3.  Show SkyGuard flag it in real time, walk through the evidence
    (temporal + cross-sensor + cross-station).
4.  Show the classification ("probable sensor spike"), trust score drop,
    and plain-English explanation.
5.  Trigger the Cascade Impact Simulator: show what a false heatwave
    alert would have looked like if this reading had gone uncaught ---
    this is the standout moment.
6.  Show the suggested corrected value, with Accept/Reject/Review
    controls --- raw data untouched.
7.  Open that sensor's Digital Twin --- show its health score declining
    over recent injected faults, and its new position in the maintenance
    queue.
8.  Run a second scenario: a coordinated heat event across several
    nearby stations --- show SkyGuard correctly identifies it as genuine
    weather, not a sensor fault, and suppresses a false alarm.
9.  Close on the Network Health view and the one-line pitch.

------------------------------------------------------------------------

# 56. SECURITY AND DATA INTEGRITY

Even for a hackathon, implement basic safeguards.

## Raw-data immutability

Raw readings should never be overwritten by correction.

## Audit trail

Every human action:

``` text
accept
reject
review
```

should be stored.

## Environment variables

Do not commit:

``` text
DATABASE_URL
API_KEYS
AWS_KEYS
```

Use:

``` text
.env
.env.example
```

## Input validation

Use Pydantic.

Reject:

-   malformed timestamps,
-   missing required fields,
-   wrong types,
-   invalid station IDs.

------------------------------------------------------------------------

# 57. DEPLOYMENT

Source blueprint recommendation:

-   Docker,
-   Vercel/Railway.

Recommended architecture:

``` text
Frontend
   ↓
Backend API
   ↓
PostgreSQL
   ↓
ML artifacts
```

Docker should package backend and dependencies.

## Clean-machine test

A teammate who did not build the environment should run:

``` text
git clone ...
docker compose up
```

and reach the application.

If that does not work, deployment is not complete.

------------------------------------------------------------------------

# 58. OBSERVABILITY

Add:

``` text
request logging
inference timing
WebSocket connection count
replay status
model load status
database errors
```

Dashboard can have a small:

``` text
System Status: ONLINE
ML Engine: READY
Database: CONNECTED
Realtime: LIVE
```

------------------------------------------------------------------------

# 59. FAILURE MODES

The system should degrade gracefully.

## ML unavailable

Fall back to:

``` text
statistical + rule-based detection
```

and mark:

``` text
ML unavailable
```

## Database unavailable

Do not claim data was saved.

Show:

``` text
Storage unavailable
```

## WebSocket unavailable

Frontend should show:

``` text
RECONNECTING
```

and optionally allow replay refresh.

## Missing neighboring stations

Lower cross-station confidence rather than assuming agreement.

The source blueprint explicitly notes that cross-station correlation
needs geographically close reference stations and confidence can be
weaker in sparse-network regions.

------------------------------------------------------------------------

# 60. HONEST LIMITATIONS --- MUST BE IN PRESENTATION

The source blueprint requires these limitations to be stated clearly.

## 1. Synthetic fault labels

There is no public dataset with large-scale verified sensor-fault
labels.

Therefore evaluation uses synthetically injected faults with known
ground truth.

## 2. Simplified Cascade rule

The Cascade Impact Simulator is illustrative and is not the real IMD
forecasting model.

## 3. Real-time demo

If replay is used, "real-time" means timed replay of
historical/synthetic data, not a production AWS feed.

## 4. Sparse network

Cross-station reasoning is weaker where geographically close reference
stations are unavailable.

## 5. No silent self-healing

Corrections are proposed and human-approved.

Raw readings are always preserved.

------------------------------------------------------------------------

# 61. JUDGING ALIGNMENT

The source blueprint maps SkyGuard to:

  ------------------------------------------------------------------------
  Criterion                                   Weight SkyGuard response
  --------------------- ---------------------------- ---------------------
  Innovation & Novelty                           25% Weather-vs-Sensor
                                                     reasoning + Trust
                                                     Score + Digital
                                                     Twin + Cascade

  Detection Accuracy                             20% Hybrid statistical +
                                                     ML ensemble

  Real-Time Capability                           15% Streaming/replay +
                                                     measured latency

  Explainability                                 10% Plain-English
                                                     evidence chain

  Scalability                                    10% Station → district →
                                                     state/network
                                                     architecture

  Practical                                      10% FastAPI + Docker
  Deployability                                      

  Visualization / UI                              5% Command Center +
                                                     map + investigation +
                                                     maintenance

  Energy Efficiency                               5% Optional edge
                                                     extension
  ------------------------------------------------------------------------

------------------------------------------------------------------------

# 62. WHY THIS IS STRONGER THAN A NORMAL ANOMALY DETECTOR

Typical project:

``` text
Input
 ↓
ML model
 ↓
Anomaly
 ↓
Dashboard
```

SkyGuard:

``` text
Input
 ↓
Validation
 ↓
Features
 ↓
Statistical evidence
 +
ML evidence
 ↓
Temporal consistency
 +
Cross-sensor consistency
 +
Cross-station consistency
 +
Persistence
 ↓
Weather-vs-Sensor reasoning
 ↓
Fault type
 ↓
Trust score
 ↓
Explanation
 ↓
Suggested correction
 ↓
Human approval
 ↓
Digital Twin
 ↓
Maintenance priority
 ↓
Cascade impact
 ↓
Live dashboard
```

The story is therefore:

> **Detection → Decision → Explanation → Correction → Health → Action →
> Impact**

------------------------------------------------------------------------

# 63. PROJECT ACCEPTANCE CRITERIA

The project should not be called complete until all are true.

## Data

-   [ ] Real public data loaded.
-   [ ] At least 10 stations targeted for strong demo.
-   [ ] T/P/H available.
-   [ ] Data dictionary complete.
-   [ ] Validation pipeline reproducible.
-   [ ] 500--2,000 synthetic fault events targeted.

## ML

-   [ ] Baseline detector.
-   [ ] Isolation Forest.
-   [ ] Autoencoder.
-   [ ] Evaluation metrics.
-   [ ] Standard inference wrapper.

## Reasoning

-   [ ] Temporal consistency.
-   [ ] Cross-sensor consistency.
-   [ ] Cross-station consistency.
-   [ ] Persistence.
-   [ ] Weather-vs-Sensor decision.
-   [ ] Fault classification.
-   [ ] Trust score.
-   [ ] Explanation.

## Correction

-   [ ] Suggested value.
-   [ ] Method.
-   [ ] Confidence.
-   [ ] Accept.
-   [ ] Reject.
-   [ ] Review.
-   [ ] Raw value preserved.

## Digital Twin

-   [ ] Sensor health.
-   [ ] Trend.
-   [ ] Fault history.
-   [ ] Maintenance priority.

## Backend

-   [ ] FastAPI.
-   [ ] PostgreSQL/Supabase.
-   [ ] REST APIs.
-   [ ] WebSockets.
-   [ ] Replay.

## Frontend

-   [ ] Command Center.
-   [ ] Map.
-   [ ] Investigation.
-   [ ] Digital Twin.
-   [ ] Maintenance.
-   [ ] Cascade.

## Validation

-   [ ] Precision.
-   [ ] Recall.
-   [ ] F1.
-   [ ] False alarm rate.
-   [ ] Detection latency.
-   [ ] Correction MAE/RMSE.
-   [ ] Degradation warning time.
-   [ ] Cascade scenarios.

## Deployment

-   [ ] Docker.
-   [ ] `.env.example`.
-   [ ] Clean-machine setup.
-   [ ] Demo dataset.
-   [ ] Backup demo.

------------------------------------------------------------------------

# 64. DAILY TEAM WORKFLOW

Every workday:

## 10-minute stand-up

Each person answers:

``` text
Yesterday:
Today:
Blocked by:
```

## Shared board

Columns:

``` text
BACKLOG
READY
IN PROGRESS
REVIEW
INTEGRATION
DONE
BLOCKED
```

## Rule

A blocker lasting more than one working session must be raised to the
whole team.

------------------------------------------------------------------------

# 65. PR CHECKLIST

Before merging:

``` text
[ ] Does it run?
[ ] Does it follow folder structure?
[ ] Is there a test or validation?
[ ] Is the interface documented?
[ ] Does it break another module?
[ ] Is there hardcoded local data?
[ ] Are secrets excluded?
[ ] Is the output reproducible?
[ ] Can another teammate understand it?
```

------------------------------------------------------------------------

# 66. FINAL ONE-LINE PITCH

> "Other systems ask: 'Is this reading anomalous?' SkyGuard asks: 'Is
> the weather anomalous, or is the sensor lying --- and what would have
> happened if we hadn't caught it?' Then it explains, corrects safely,
> tracks sensor health, and shows the disaster it just prevented."

------------------------------------------------------------------------

# 67. FINAL TEAM EXECUTION ORDER

If the team is confused about what to do first, follow exactly this
order:

``` text
1. Git repository
        ↓
2. Data contract
        ↓
3. Real historical data
        ↓
4. Data cleaning + validation
        ↓
5. EDA
        ↓
6. Fault injection
        ↓
7. Feature engineering
        ↓
8. Statistical baseline
        ↓
9. Isolation Forest
        ↓
10. Autoencoder
        ↓
11. Hybrid detector
        ↓
12. Weather-vs-Sensor engine
        ↓
13. Trust score + explanation
        ↓
14. Correction engine
        ↓
15. Digital Twin
        ↓
16. Maintenance queue
        ↓
17. PostgreSQL database
        ↓
18. FastAPI
        ↓
19. WebSockets
        ↓
20. Frontend static UI
        ↓
21. Frontend API integration
        ↓
22. Real-time replay
        ↓
23. Cascade simulator
        ↓
24. Validation
        ↓
25. Docker
        ↓
26. Demo rehearsal
```

------------------------------------------------------------------------

# 68. CRITICAL RULES FOR THE TEAM

1.  **Do not build six disconnected projects.**
2.  **Do not start with frontend polish before the data/API contract
    exists.**
3.  **Do not train ML on dirty, unexplained data.**
4.  **Do not use synthetic faults without ground-truth labels.**
5.  **Do not randomly split highly correlated time-series rows without
    considering leakage.**
6.  **Do not call model scores "confidence" until they are calibrated or
    clearly described as scores.**
7.  **Do not overwrite raw readings.**
8.  **Do not let the frontend invent ML decisions.**
9.  **Do not claim a real IMD forecasting model when using a toy Cascade
    rule.**
10. **Do not claim a production live AWS feed when demonstrating
    replay.**
11. **Do not wait for all modules to finish before integrating.**
12. **Always maintain one deterministic demo path.**

------------------------------------------------------------------------

# 69. THE PRODUCT STORY

The final product should communicate one simple narrative:

``` text
A number arrives.
       ↓
Is it valid?
       ↓
Is it unusual?
       ↓
Why is it unusual?
       ↓
Is the weather unusual?
OR
Is the sensor lying?
       ↓
How much do we trust it?
       ↓
What should we use instead?
       ↓
Should a human approve it?
       ↓
Is this sensor getting worse?
       ↓
Which sensor should maintenance inspect?
       ↓
What downstream alert would have happened?
```

That is SkyGuard AI.
