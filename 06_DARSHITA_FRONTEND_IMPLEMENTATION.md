# Darshita — Frontend: Working Product Implementation

## Role
**Primary:** Frontend

## Exact responsibility
Darshita answers:

> **"How do we turn the approved UI architecture into a working interactive product?"**

Medhvi specifies the information architecture. Darshita implements it.

## Stack
```text
React
Vite
Tailwind CSS
Recharts / Plotly
Leaflet
```

## Structure
```text
frontend/src/
├── components/
├── pages/
├── hooks/
├── services/
├── utils/
└── types/
```

## Pages
Implement:
```text
CommandCenter
StationMap
Investigation
DigitalTwin
Maintenance
CascadeSimulator
```

## API layer
Centralize calls:
```text
services/api.js
```

Functions:
```text
getStations()
getStation(id)
getReadings(id)
getHealth(id)
getAnomalies()
getAnomaly(id)
getMaintenance()
submitCorrection(id, action)
getCascade(id)
```

Do not duplicate fetch logic throughout components.

## Investigation implementation
Display Mitali's decision object:
```text
reading
decision
fault type
Trust Score
confidence
evidence
suggested correction
review actions
cascade action
```

Actions:
```text
ACCEPT
REJECT
REVIEW
```

Frontend must not calculate the Trust Score itself.

## Correction
Call:
```text
POST /api/corrections/{id}/accept
```

Keep:
```text
original value
suggested value
human action
timestamp
```
visually distinct.

## Digital Twin
Implement:
```text
health
trust
trend
fault history
maintenance priority
```

## Maintenance
Implement:
- filters
- sorting
- priority indicators
- reason display
- navigation to sensor investigation

## WebSocket
Connect to:
```text
/ws/live
```

Handle:
```text
reading
anomaly
trust_update
digital_twin_update
maintenance_update
cascade_ready
```

Connection states:
```text
LIVE
RECONNECTING
OFFLINE
REPLAY MODE
```
These states are specified in the existing plan. fileciteturn2file9L1331-L1338

## Replay controls
Implement:
```text
START
PAUSE
RESUME
RESET
SPEED
```
fileciteturn2file3L423-L433

## Cascade
Display:
```text
WITHOUT SKYGUARD
WITH SKYGUARD
IMPACT SUMMARY
```

Clearly show that the downstream model is illustrative, not the real IMD forecasting model. fileciteturn2file3L504-L514

## Error states
Must handle:
```text
API unavailable
database unavailable
ML unavailable
WebSocket disconnected
missing station
empty anomaly list
```

For ML unavailable, backend may fall back to statistical/rule-based detection and explicitly mark ML unavailable. fileciteturn2file6L900-L917

## Does NOT own
- anomaly models
- fault injection
- data collection
- reasoning
- Trust Score
- database business logic
- WebSocket backend

## Deliverables
```text
frontend/src/pages/
frontend/src/components/
frontend/src/hooks/
frontend/src/services/
frontend/src/types/
```

## Verification
Test:
- [ ] real API
- [ ] empty API
- [ ] loading
- [ ] API error
- [ ] WebSocket disconnect
- [ ] reconnect
- [ ] replay
- [ ] correction actions
- [ ] responsive layout

## One-line ownership
> **Darshita turns SkyGuard's backend intelligence and Medhvi's visual specification into the working interactive application.**
