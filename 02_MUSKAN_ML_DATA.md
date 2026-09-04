# SkyGuard AI --- Muskan Execution Plan

## Role

**Primary:** ML + Data Collection

## Core ownership

Muskan owns the reproducible dataset and model-training pipeline.

## Phase 0

Set up:

``` text
data/raw
data/interim
data/processed
data/synthetic
ml/artifacts
```

Create a data README describing: - source, - download date, - station
selection, - variables, - transformations.

## Phase 1 --- Data Collection

Target from the source blueprint: - 10--20 stations, - 3--6 months, -
hourly, - Temperature, - Pressure, - Humidity.

Do not modify raw files.

## Phase 2 --- Fault Injection Lab

Implement:

``` python
inject_spike()
inject_drift()
inject_flatline()
inject_dropout()
inject_abrupt_jump()
inject_cross_sensor_inconsistency()
```

Every generated event must have:

``` text
event_id
station_id
variable
fault_type
start
end
clean_value
faulty_value
severity
seed
```

Use a fixed random seed.

## Fault design

### Spike

One/few observations become abnormally high or low.

### Drift

Small changes accumulate over time.

### Flatline

Sensor repeats nearly the same value.

### Dropout

Observations disappear.

### Jump

A persistent step change occurs.

### Multivariate inconsistency

One variable changes while related variables do not support the same
behavior.

## Phase 3 --- Dataset generation

Target: **500--2,000 synthetic fault events** across all types.

Do not place all faults into one station.

Distribute by: - station, - variable, - season/time period, -
severity, - duration.

## Phase 4 --- Training baseline

Prepare clean training data.

Avoid contamination: - faulted examples should not accidentally enter
the normal-only training set for the Autoencoder.

## Phase 5 --- ML

Train: 1. Isolation Forest. 2. Autoencoder.

Save:

``` text
model
scaler
feature schema
threshold
training metadata
```

## Phase 6 --- Inference wrapper

Expose one stable function:

``` python
predict(features)
```

Return:

``` json
{
  "is_anomaly": true,
  "anomaly_score": 0.91,
  "model_version": "..."
}
```

## Phase 12 --- Validation

Create a benchmark table:

  Fault            Precision   Recall   F1   False alarms
  -------------- ----------- -------- ---- --------------
  Spike                                    
  Drift                                    
  Flatline                                 
  Dropout                                  
  Jump                                     
  Multivariate                             

## Final artifacts

``` text
fault_injector.py
dataset_generator.py
training_pipeline.py
model artifacts
benchmark.csv
training README
```

## Muskan's success criterion

Someone else can: 1. take clean data, 2. run the injector, 3. reproduce
the labeled benchmark, 4. train/load the models, 5. get the same general
pipeline outputs.
