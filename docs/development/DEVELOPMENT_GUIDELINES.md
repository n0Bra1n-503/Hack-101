# SkyGuard AI — Development Guidelines & Engineering Standards

## 1. Scope & Purpose

This document establishes the mandatory software engineering standards, architectural boundaries, and development principles for all contributors working on **SkyGuard AI**, with specific focus on **Mitali's module** (Decision Intelligence, Backend Integration & Risk Integration).

Adherence to these rules guarantees system stability, testability, auditability, safety, and clean integration across all six sub-teams.

---

## 2. The Ten Golden Rules of SkyGuard AI

### Rule 1: No Business Logic in API Routes
* API routes (`backend/app/api/`) are strictly reserved for:
  * Transport handling (HTTP request parsing, status codes, query/path parameters).
  * Payload validation via Pydantic schemas.
  * Delegating execution to appropriate service functions (`backend/app/services/`).
  * Returning serialized responses.
* No mathematical computations, risk calculations, database transactions, ML calls, or data transformations are permitted directly inside route handlers.

### Rule 2: Never Overwrite Raw Weather Data
* Raw sensor telemetry is an immutable historical observation record.
* Once written to persistent storage, raw reading rows must **never** be updated, overwritten, or deleted in place.
* Suggested corrections and imputed estimates exist exclusively as separate relational records in the `corrections` table, referencing the original `reading_id`.
* The review lifecycle (`SUGGESTED` $\to$ `PENDING_REVIEW` $\to$ `ACCEPTED` / `REJECTED`) ensures full scientific traceability and audit compliance.

### Rule 3: `anomaly_score != trust_score`
* An anomaly score measures **statistical rarity** ($0.0 \to 1.0$), while a Trust Score measures **operational dependability** ($0 \to 100$).
* A genuine extreme meteorological phenomenon (e.g., severe squall line or flash heatwave) will exhibit a high anomaly score, yet possess a high Trust Score because cross-station corroboration confirms it is authentic.
* Conversely, an isolated hardware glitch (e.g., sensor pin short) yields a high anomaly score but a very low Trust Score.
* Trust Score must always be calculated through multidimensional evidence synthesis, never as an inversion of an anomaly score.

### Rule 4: Extreme Reading Does Not Directly Create Disaster Risk
* **Safety Invariant**: Under no circumstances may an extreme telemetry value directly trigger a disaster alert or hazard warning:
  $$\text{extreme reading} \not\longrightarrow \text{disaster alert}$$
* Telemetry must always traverse:
  1. Anomaly detection
  2. Temporal consistency
  3. Cross-sensor thermodynamic consistency
  4. Cross-station spatial consistency
  5. Weather-vs-sensor root cause classification
* Only observations classified as authentic `genuine_weather` advance to event validation and risk assessment.

### Rule 5: `sensor_fault` Blocks Disaster Risk
* If the decision engine classifies an atypical observation as a `sensor_fault`, the pipeline **strictly terminates** any progression to disaster event creation.
* Hardware failures route exclusively to:
  * Trust Score downgrading
  * Fault archetype classification
  * Imputed correction generation
  * Digital Twin degradation logging
  * Field maintenance queue dispatch

### Rule 6: `uncertain` Blocks Automatic Public Risk
* When evidence is conflicting, spatial station coverage is sparse, or confidence is borderline, the system classifies the observation as `uncertain`.
* The system **never** forces an uncertain case into a binary decision.
* Automated public risk warnings are **strictly prohibited** for uncertain observations; these cases are flagged for human meteorologist inspection.

### Rule 7: Public APIs Hide Engineering Internals
* Public-facing endpoints (`/api/public/risk/{area}`) serve citizens, civic apps, and community stakeholders.
* Public payloads must **never expose**:
  * Internal sensor hardware IDs (e.g., `SNS-TMP-104`)
  * Internal fault diagnostic codes (e.g., `multivariate_inconsistency`)
  * ML model class names, versions, or raw weights
  * Internal stack traces, raw error payloads, or debug logs
* Public responses provide clean, non-technical hazard explanations and actionable safety guidance.

### Rule 8: Official Advisories Are Never Fabricated
* The system must **never manufacture or fabricate** official advisories from government agencies (e.g., IMD, NDMA, State Disaster Management Authorities).
* Do not claim "IMD issued a Red Alert" or "NDMA ordered evacuations" unless an authenticated, verified external official feed has been integrated.
* Default status for public advisories is:
  `official_advisory_status: "check_official_sources"`.
* When no validated hazard is active, return:
  `{"status": "no_validated_risk", "area": "..."}`.

### Rule 9: Team Modules Communicate Through Stable Contracts
* Sub-teams collaborate exclusively across formal contracts documented in `docs/contracts/DATA_CONTRACTS.md`.
* Backend routes must interact with ML models via decoupled adapters (`ml/integration/`) rather than importing model training scripts, internal tensors, or file formats directly.
* Changes to internal implementations must not break public schemas, serialized payloads, or field types.

### Rule 10: Standard Module Quality Gate
Every functional module implementation across all project phases must satisfy the complete engineering lifecycle before completion:
$$\text{Code} + \text{Docs} + \text{Sample Input} + \text{Sample Output} + \text{Test} + \text{Commit} + \text{Integration Check}$$
No phase is considered complete without passing all automated tests and verifying schema compliance.

---

## 3. Git & Branching Conventions

* **Baseline Branch**: `mitali`
* **Active Development Branch**: `mitali-skyguard-integration`
* **Commit Message Format**: Adhere strictly to Conventional Commits:
  * `feat:` A new feature or capability.
  * `fix:` A bug fix.
  * `docs:` Documentation or architectural contract updates.
  * `refactor:` Code restructuring without behavior alteration.
  * `test:` Adding or updating automated test suites.
  * `chore:` Dependencies, build scripts, or tool configuration.
* **Prohibitions**:
  * **Never commit directly to `main`**.
  * **Never modify `main`**.
  * **Never merge into `main` without explicit peer review and authorization**.
  * **Never force push (`git push --force`) to shared team branches**.

---

## 4. Phase 1 Implementation Flow: Backend Foundation & Ingestion

The implemented Phase 1 pipeline follows the strict layered execution flow:

```text
data source
     ↓
POST /api/readings
     ↓
Pydantic validation
     ↓
ingestion service
     ↓
database
     ↓
retrieval API
```

### Core Phase 1 Scope Boundaries:
1. **Structural Validation Only**: Phase 1 validates syntax, mandatory fields, numeric types, and coordinate ranges.
2. **No Weather Authenticity Determination**: Phase 1 **does NOT** determine whether weather is genuine or faulty.
3. **Acceptance of Extreme Observations**: Extreme readings (e.g., `temperature = 55.0°C`) are structurally valid and are accepted with `HTTP 201 Created`. Anomaly detection, Trust Scoring, and weather-vs-sensor classification belong exclusively to subsequent phases.
4. **Raw Data Immutability**: All ingested readings are stored as immutable records in the `readings` table. Duplicates are rejected with `HTTP 409 Conflict`.
