# SkyGuard AI --- Medhvi Execution Plan

## Role

**Primary:** Frontend + EDA

## Mission

Turn the analytical system into an operational command center that a
judge can understand immediately.

## Phase 0 --- UI foundation

Set up:

``` text
frontend/
React
Vite
Tailwind CSS
```

Create:

``` text
components/
pages/
layouts/
services/
hooks/
types/
utils/
```

## Phase 1 --- Translate EDA into visual requirements

Medhvi should review EDA with Manan and Neha and decide: - which
patterns need a chart, - which values need cards, - which evidence needs
badges, - which anomalies need a timeline.

## Design direction

The UI should feel like: \> meteorological operations + data-quality
command center

Avoid: - generic admin-dashboard appearance, - excessive gradients, -
unnecessary decorative animations, - too many charts.

## Main screens

### 1. Command Center

Top cards:

``` text
Total Stations
Healthy
Degrading
Critical
Active Anomalies
Average Trust
```

Main: - live map, - anomaly feed, - trust distribution, - maintenance
preview.

### 2. Station Map

Use Leaflet.

Marker states:

``` text
green = healthy
amber = suspicious
red = critical
```

### 3. Investigation

Show: - raw reading, - recent time series, - trust score, -
confidence, - evidence, - fault type, - correction, - actions.

### 4. Digital Twin

Show: - health, - trend, - current trust, - fault count, - timeline, -
maintenance priority.

### 5. Maintenance

Table:

``` text
Priority
Sensor
Health
Trust
Trend
Faults
Reason
Action
```

### 6. Cascade

Use a strong before/after visual.

## Reusable components

``` text
TrustScore
StatusBadge
MetricCard
StationMap
LiveAnomalyFeed
TimeSeriesChart
EvidencePanel
CorrectionCard
DigitalTwinTimeline
MaintenanceTable
CascadePanel
ConnectionIndicator
```

## Frontend states

Every page needs: - loading, - empty, - error, - connected, -
disconnected, - replay.

## Phase 9 --- Backend integration

Use backend contracts instead of hardcoding.

Create:

``` text
services/api.ts
services/websocket.ts
```

## Phase 10 --- Real-time

Show:

``` text
LIVE
RECONNECTING
OFFLINE
REPLAY MODE
```

New anomalies should animate subtly into the feed.

## Phase 11 --- Cascade

Make the Cascade moment visually unforgettable.

Example:

``` text
55°C bad reading
      ↓
WITHOUT SKYGUARD
FALSE HEATWAVE ALERT
      ↓
WITH SKYGUARD
NO FALSE ALERT
```

## Final quality checklist

-   [ ] Desktop-first polished UI
-   [ ] Responsive
-   [ ] No broken overflow
-   [ ] Charts readable
-   [ ] Trust score prominent
-   [ ] Evidence readable
-   [ ] Buttons work
-   [ ] WebSocket states visible
-   [ ] No mock data remains in final demo unless explicitly marked
