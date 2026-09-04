# SkyGuard AI — AWS Raw Data Format

This document defines the standard JSON format for raw Automatic Weather Station (AWS) observations used by the **SkyGuard AI** anomaly detection and sensor reliability pipeline.

The raw data contains the original sensor observations. Machine-learning features such as lag values, rolling statistics, rate of change, anomaly scores, and trust scores are generated later by the SkyGuard processing pipeline.

---

## 1. Purpose

SkyGuard AI analyzes AWS sensor data to determine whether an unusual observation represents:

* Genuine weather conditions
* Sensor malfunction or failure
* An uncertain condition requiring further analysis

The raw input data should contain the original sensor measurements without manually generated ML features.

---

## 2. Required Data Fields

Each observation should contain the following fields:

| Field                  | Type   | Unit     | Required | Description                          |
| ---------------------- | ------ | -------- | -------- | ------------------------------------ |
| `timestamp`            | String | ISO 8601 | Yes      | Date and time of the observation     |
| `station_id`           | String | —        | Yes      | Unique identifier of the AWS station |
| `temperature`          | Number | °C       | Yes      | Air temperature                      |
| `relative_humidity`    | Number | %        | Yes      | Relative humidity                    |
| `atmospheric_pressure` | Number | hPa      | Yes      | Atmospheric/barometric pressure      |

### Optional Station Metadata

If available in the original AWS dataset, the following fields may also be included:

| Field       | Type   | Unit    | Required | Description       |
| ----------- | ------ | ------- | -------- | ----------------- |
| `latitude`  | Number | degrees | No       | Station latitude  |
| `longitude` | Number | degrees | No       | Station longitude |
| `altitude`  | Number | meters  | No       | Station elevation |

**Important:** Optional fields should only be included when they are actually available in the source dataset. Do not create artificial values.

---

## 3. Standard JSON Format

A single AWS observation should follow this structure:

```json
{
  "timestamp": "2026-08-15T14:30:00",
  "station_id": "AWS_001",
  "temperature": 31.4,
  "relative_humidity": 62.8,
  "atmospheric_pressure": 1008.6
}
```

If station metadata is available:

```json
{
  "timestamp": "2026-08-15T14:30:00",
  "station_id": "AWS_001",
  "temperature": 31.4,
  "relative_humidity": 62.8,
  "atmospheric_pressure": 1008.6,
  "latitude": 18.5204,
  "longitude": 73.8567,
  "altitude": 560
}
```

---

## 4. Multiple Observations

A complete dataset can contain an array of observations:

```json
[
  {
    "timestamp": "2026-08-15T14:30:00",
    "station_id": "AWS_001",
    "temperature": 31.4,
    "relative_humidity": 62.8,
    "atmospheric_pressure": 1008.6
  },
  {
    "timestamp": "2026-08-15T14:31:00",
    "station_id": "AWS_001",
    "temperature": 31.5,
    "relative_humidity": 62.5,
    "atmospheric_pressure": 1008.4
  },
  {
    "timestamp": "2026-08-15T14:32:00",
    "station_id": "AWS_001",
    "temperature": 31.5,
    "relative_humidity": 62.3,
    "atmospheric_pressure": 1008.5
  }
]
```

Each object represents one observation at a specific point in time.

---

## 5. Data Requirements

### Timestamp

Timestamps should preferably use the ISO 8601 format:

```text
YYYY-MM-DDTHH:MM:SS
```

Example:

```text
2026-08-15T14:30:00
```

Observations should be chronologically ordered whenever possible.

### Station ID

Every observation should contain a consistent station identifier.

Example:

```text
AWS_001
AWS_002
AWS_PASHAN
```

The same station should always use the same `station_id`.

### Temperature

Temperature should be represented as a numeric value in degrees Celsius.

Example:

```json
"temperature": 31.4
```

### Relative Humidity

Relative humidity should be represented as a percentage from the sensor.

Example:

```json
"relative_humidity": 62.8
```

### Atmospheric Pressure

Atmospheric pressure should preferably be represented in hectopascals (hPa).

Example:

```json
"atmospheric_pressure": 1008.6
```

If the original dataset uses another unit, the values should be converted before being used by the ML pipeline.

---

## 6. Missing Values

Missing sensor measurements should **not** be replaced with artificial values such as `0`.

For example, if temperature is unavailable:

```json
{
  "timestamp": "2026-08-15T14:30:00",
  "station_id": "AWS_001",
  "temperature": null,
  "relative_humidity": 62.8,
  "atmospheric_pressure": 1008.6
}
```

The pipeline can then handle missing values during preprocessing.

---

## 7. Do Not Add ML Features to Raw Data

The raw JSON should contain the original sensor observations.

Do **not** manually add fields such as:

```text
temperature_zscore
temperature_rolling_mean
temperature_delta
pressure_rate_of_change
humidity_lag
anomaly_score
trust_score
fault_type
```

These are derived features or model outputs and should be generated by the SkyGuard pipeline.

The intended processing flow is:

```text
Raw AWS Data
     │
     ▼
Data Validation
     │
     ▼
Feature Engineering
     │
     ├── Temporal Features
     ├── Lag Features
     ├── Rolling Statistics
     ├── Rate of Change
     └── Cross-Sensor Features
     │
     ▼
Statistical Detection
     │
     ▼
Isolation Forest
     │
     ▼
Autoencoder
     │
     ▼
Hybrid Evidence Engine
     │
     ▼
Weather vs Sensor Decision
     │
     ▼
Trust Score + Explanation
```

---

## 8. Training vs Inference Data

The same raw observation format can be used for both training and inference.

### Training

For model training, the pipeline uses historical/reference AWS observations to learn normal sensor behavior.

Controlled fault injection may then be applied to create labeled data for evaluating anomaly detection performance.

```text
Clean AWS Data
      ↓
Feature Engineering
      ↓
Model Training
      ↓
Fault Injection
      ↓
Evaluation
```

### Real-Time Inference

During real-time operation, new AWS observations are passed to the trained pipeline sequentially:

```text
AWS Sensor Reading
        ↓
Data Validation
        ↓
Feature Generation
        ↓
Anomaly Detection
        ↓
Evidence Analysis
        ↓
Decision
        ↓
Trust Score
```

---

## 9. Example Dataset

Example file:

```text
aws_data.json
```

Contents:

```json
[
  {
    "timestamp": "2026-08-15T14:30:00",
    "station_id": "AWS_001",
    "temperature": 31.4,
    "relative_humidity": 62.8,
    "atmospheric_pressure": 1008.6
  },
  {
    "timestamp": "2026-08-15T14:31:00",
    "station_id": "AWS_001",
    "temperature": 31.5,
    "relative_humidity": 62.5,
    "atmospheric_pressure": 1008.4
  },
  {
    "timestamp": "2026-08-15T14:32:00",
    "station_id": "AWS_001",
    "temperature": 31.5,
    "relative_humidity": 62.3,
    "atmospheric_pressure": 1008.5
  }
]
```

---

## 10. Important Data Handling Rules

1. Preserve the original sensor values.
2. Do not replace missing values with `0`.
3. Use consistent units across the dataset.
4. Keep timestamps in chronological order.
5. Maintain a consistent `station_id`.
6. Do not manually calculate ML features in the raw dataset.
7. Do not add anomaly labels to real-world data unless those labels are actually known.
8. Keep the raw dataset separate from generated/processed datasets.
9. Do not overwrite the original raw CSV.
10. Validate the real AWS dataset before training models.

---

## 11. Recommended Directory Structure

```text
data/
├── raw/
│   └── aws_data.json
│
├── processed/
│   └── features.csv
│
└── injected/
    └── fault_injected_data.csv
```

The `raw/` directory should contain the original AWS data without ML-generated features.

---

## 12. Data Conversion

If the original AWS data is provided as CSV, it should first be inspected and mapped to the SkyGuard schema before conversion.

Example:

```text
AWS CSV
   ↓
Column Mapping
   ↓
Unit Conversion
   ↓
Timestamp Normalization
   ↓
Missing-Value Handling
   ↓
SkyGuard Raw JSON
```

The exact column mapping depends on the actual AWS dataset. **Do not assume that the original CSV column names or units match the SkyGuard schema.**

---

## 13. Final Raw Data Schema

The minimum accepted observation is:

```text
timestamp
station_id
temperature
relative_humidity
atmospheric_pressure
```

Optional metadata:

```text
latitude
longitude
altitude
```

Everything else should be treated as dataset-specific and evaluated before being added to the pipeline.

---

**SkyGuard AI — Raw AWS Data Specification**

This format is intended to provide a consistent interface between real AWS sensor data and the SkyGuard AI anomaly detection pipeline.
