# SkyGuard AI --- Manan Execution Plan

## Role

**Primary:** ML + EDA\
**Team:** SkyGuard AI

## Core ownership

Manan owns the analytical/ML side that turns raw weather observations
into measurable anomaly evidence.

### Primary modules

``` text
notebooks/
ml/features/
ml/detectors/
ml/evaluation/
ml/scoring/
```

## Phase 0 --- Repository

Tasks: - Clone repository. - Create ML branch. - Read data contract. -
Read API/inference contract. - Add ML issue labels. - Create
`ml/README.md`.

Deliverable: - ML environment runs locally.

## Phase 1 --- EDA

Required questions: 1. What does normal temperature behavior look like?
2. What does normal pressure behavior look like? 3. What does normal
humidity behavior look like? 4. How strong are daily patterns? 5. How
different are stations? 6. How much missingness exists? 7. How
correlated are nearby stations? 8. Which transformations make sense?

Required notebooks:

``` text
01_data_audit.ipynb
02_eda_temperature.ipynb
03_eda_pressure.ipynb
04_eda_humidity.ipynb
```

Required charts: - time-series, - histogram, - boxplot, - rolling
mean, - rolling standard deviation, - station comparison, - correlation
matrix, - missingness.

## Phase 2 --- Fault Injection Support

Work with Muskan to verify that: - spikes are realistic enough for a
benchmark, - drift is gradual, - flatline duration varies, - dropout
intervals vary, - multivariate inconsistencies are labeled correctly.

Create plots comparing:

``` text
clean
fault-injected
ground truth
```

## Phase 3 --- Feature Engineering

Build reusable functions for:

``` text
rolling_mean
rolling_std
delta
rate_of_change
hour
day_of_year
sin_hour
cos_hour
neighbor_mean
neighbor_difference
cross_sensor_change
```

Critical rule: \> Training and inference must call the same feature
implementation.

## Phase 4 --- Statistical Baseline

Implement: - range/rule checks, - z-score, - rolling z-score, - EWMA, -
persistence.

Output:

``` json
{
  "statistical_score": 0.0,
  "rule_flags": [],
  "persistence_score": 0.0
}
```

## Phase 5 --- ML

Work with Muskan on: - Isolation Forest, - Autoencoder.

Manan should focus heavily on: - feature selection, - threshold
evaluation, - false positives, - station generalization, - temporal
leakage.

## Phase 6 --- Reasoning Evidence

Provide Mitali with structured evidence, not prose.

Example:

``` json
{
  "ml_anomalous": true,
  "isolation_score": 0.91,
  "autoencoder_error": 0.83,
  "temporal_deviation": 0.94,
  "cross_station_agreement": 0.08,
  "cross_sensor_agreement": 0.12,
  "persistence": 0.20
}
```

## Phase 7 --- Trust Score

Help Mitali validate the score.

Do not blindly equate:

``` text
anomaly score = confidence
```

Calibrate or label clearly.

## Phase 8 --- Digital Twin

Provide: - anomaly frequency, - degradation trend, - recent fault
counts, - severity, - early warning signal.

## Phase 12 --- Final Validation

Own the final evaluation report.

Metrics: - Precision, - Recall, - F1, - false alarm rate, - detection
latency, - correction MAE/RMSE, - degradation warning time.

## Required final artifacts

``` text
feature_pipeline.py
baseline_detector.py
evaluation.py
model_evaluation_report.md
EDA notebooks
plots
metrics.json
```

## Manan's final success criterion

A judge asks: \> "How do you know the model works?"

Manan should be able to answer with: - test protocol, - held-out data, -
metrics, - false-alarm analysis, - examples of genuine weather vs sensor
faults.
