# Darshita — Frontend: React Implementation, UX Interactions & Public Safety View

## Role
**Primary:** Frontend

## Main Question
> How do we turn Medhvi's information architecture into a working product?

## Core Ownership
- React implementation
- page routing
- reusable components
- API integration
- frontend state
- loading/error states
- responsive behavior
- UX interactions
- WebSocket states
- replay controls
- correction actions
- Digital Twin interface
- maintenance interface
- cascade interface

## Existing Pages

```text
CommandCenter
StationMap
Investigation
DigitalTwin
Maintenance
CascadeSimulator
```

## New Page — Disaster Risk

Implement Medhvi's design.

Show:
- event
- risk level
- confidence
- area
- validated status
- evidence
- affected stations

Example:

```text
HIGH RISK
Extreme Heat

Delhi
Confidence 96%

✓ Multiple stations agree
✓ Event persisted
✓ Sensor reliability verified
```

## New Page — Citizen Safety

Create a simple public-facing experience.

Answer:

```text
What is happening?
How serious is it?
Where?
How confident is the system?
What should I do?
```

Example:

```text
Delhi

HIGH HEAT RISK

44°C

Confidence: 96%

Multiple nearby weather stations
confirm the condition.

General guidance:
• Stay hydrated
• Avoid prolonged outdoor exposure

Check official government advisories
for authoritative warnings.
```

Do not present SkyGuard as an official government warning authority.

## Public View Must Be Simpler

Do not show:
- anomaly model names
- raw sensor IDs
- complex Trust Score breakdown
- internal fault codes
- backend/debug information

## API Layer

Centralize calls:

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

getRisks()
getRisk(id)
getAreaRisk(area)
getPublicRisk(area)
```

## Frontend Must Not Calculate

The frontend must NOT calculate:
- Trust Score
- anomaly score
- risk score
- weather-vs-sensor decision

It only displays backend outputs.

## Error States

Handle:
- API unavailable
- empty risk data
- missing area
- ML unavailable
- database unavailable
- WebSocket disconnected
- loading
- offline/reconnecting

## Success Criterion

The interface should let a judge follow:
bad reading → detection → reasoning → correction → sensor health → maintenance → validated event → disaster risk → citizen/public output.
