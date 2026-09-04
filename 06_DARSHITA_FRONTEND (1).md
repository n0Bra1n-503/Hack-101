# SkyGuard AI --- Darshita Execution Plan

## Role

**Primary:** Frontend

## Mission

Build the interactive layer that turns SkyGuard's intelligence into a
judge-friendly experience.

## Phase 0

Set up frontend and component conventions.

## Phase 1 --- Static dashboard

Build screens using mock JSON so frontend work does not wait for
backend.

## Command Center

Must show:

``` text
Network status
Total stations
Healthy
Degrading
Critical
Active anomalies
Average trust
```

Then: - station map, - live anomaly feed, - maintenance preview.

## Station map

Click station:

``` text
AWS-104
T/P/H
Trust
Health
Status
Last anomaly
```

## Investigation

Primary information hierarchy:

``` text
1. What happened?
2. Is it weather or sensor?
3. How confident are we?
4. Why?
5. What value is suggested?
6. What should I do?
```

Buttons:

``` text
ACCEPT
REJECT
REVIEW
```

## Digital Twin

Show:

``` text
Health score
Trust score
Trend
Fault history
Recent anomalies
Maintenance priority
```

## Maintenance Queue

Make priority obvious.

Example:

``` text
HIGH
AWS-104
Health 62
Trust 18
Declining
11 faults / 30d
```

## Phase 10 --- WebSocket

Subscribe to:

``` text
/ws/live
```

When a new event arrives: 1. update reading, 2. update station, 3.
update anomaly feed, 4. update trust, 5. update Digital Twin, 6. update
maintenance queue.

## Connection state

Always show:

``` text
LIVE
RECONNECTING
OFFLINE
REPLAY
```

## Phase 11 --- Cascade

Build the visual "wow" screen.

Show:

``` text
BAD READING
      ↓
SkyGuard
      ↓
WITHOUT vs WITH
```

The user should not need to understand the backend implementation.

## Demo controls

Provide:

``` text
Start Replay
Pause
Reset
Inject 55°C Spike
Run Genuine Heat Event
Run Degradation Scenario
```

These should call backend endpoints.

## UX rules

-   No dead buttons.
-   No unexplained colors.
-   No tiny labels.
-   No hidden status.
-   No excessive animations.
-   No fake "AI magic" text.
-   Show evidence.

## Final frontend acceptance

A judge should be able to follow:

``` text
Healthy network
→ bad reading
→ detection
→ reasoning
→ correction
→ Digital Twin
→ maintenance
→ cascade impact
```

without the team verbally explaining every click.
