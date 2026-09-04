# SkyGuard AI --- Neha Execution Plan

## Role

**Primary:** Data Collection + EDA

## Mission

Create the clean, trustworthy foundation on which ML and the rest of
SkyGuard depend.

## Phase 0 --- Data contract

Required core fields:

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

## Phase 1 --- Data acquisition

Target: - 10--20 stations, - 3--6 months, - hourly, - T/P/H.

For every source record: - preserve raw, - record provenance, - document
transformation.

## Data quality checks

### Missing values

Calculate:

``` text
missing count
missing percentage
missing by station
missing by variable
missing by period
```

### Duplicates

Check:

``` text
station_id + timestamp
```

### Timestamp

Check: - parseability, - ordering, - timezone, - gaps, - duplicate time
records.

### Value sanity

Flag: - impossible values, - suspicious extremes, - invalid types.

Important: \> Do not automatically delete every extreme value. A genuine
extreme weather event can be valid.

## Phase 2 --- EDA

Produce: - station coverage, - distributions, - time-series, -
correlation, - missingness, - station comparison.

## Cross-station analysis

Create station-neighbor information.

Potential metadata:

``` text
station_id
neighbor_station_id
distance
```

Do not assume all stations are valid neighbors.

## Phase 3 --- Fault injection support

Give Muskan clean windows that are safe for injection.

Validate: - no existing suspicious data in "normal" windows, - enough
temporal context before/after injection.

## Phase 6 --- Reasoning support

Provide Mitali: - station neighborhoods, - historical baselines, -
normal ranges, - missingness context.

## Data release structure

``` text
data/
├── raw/
├── interim/
├── processed/
└── synthetic/
```

## Final artifacts

``` text
data_dictionary.md
data_quality_report.md
station_metadata.csv
clean_dataset.parquet/csv
EDA notebooks
station_neighbors.csv
```

## Neha's success criterion

If someone asks: \> "Can we trust the dataset?"

The answer must be backed by: - provenance, - quality checks, -
documented transformations, - coverage statistics, - missingness
statistics.
