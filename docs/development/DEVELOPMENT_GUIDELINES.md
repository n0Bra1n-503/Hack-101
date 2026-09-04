# SkyGuard AI — Development Guidelines & Engineering Standards

## 1. Scope & Purpose

This document establishes the mandatory software engineering standards, architectural boundaries, and development principles for all contributors working on **SkyGuard AI**, with specific focus on **Mitali's module** (Decision Intelligence & Backend Integration).

Adherence to these rules guarantees system stability, testability, auditability, and clean integration across all six sub-teams.

---

## 2. The Ten Golden Rules of SkyGuard AI

### Rule 1: Do Not Put Business Logic in `main.py`
* `main.py` (when implemented in Phase 1) is strictly reserved for:
  * Application instantiation (`FastAPI(...)`).
  * Middleware registration (CORS, timing, logging).
  * Top-level lifecycle event handlers (`lifespan`, startup, shutdown).
  * Router inclusions (`app.include_router(...)`).
* No data transformation, database queries, mathematical calculations, or ML model calls are permitted directly within `main.py`.

---

### Rule 2: Strict Separation of Concerns (API, Schema, Service, Model)
Code must adhere strictly to a layered architecture:
* **`api/` (Routers)**: Handle HTTP/WebSocket transport, extract query/path parameters, invoke services, and return responses. No business logic.
* **`schemas/` (Pydantic Models)**: Define data contracts, request payloads, response serialization, and data validation rules. No database access.
* **`services/` (Business & Intelligence Logic)**: Contain all reasoning, evidence calculation, trust scoring, and workflow orchestration. Stateless wherever possible.
* **`models/` (SQLAlchemy ORM)**: Define database tables, relationships, indexes, and persistence schemas. No business rules.

---

### Rule 3: Do Not Overwrite Raw Weather Data
* Raw sensor telemetry is an immutable historical record.
* Once written to the database, a raw reading record must **never** be updated, overwritten, or truncated in place.
* Value corrections, imputed estimates, or calibration adjustments must be stored as separate records in the `corrections` table, referencing the original `reading_id`.
* The state transition of corrections (`SUGGESTED` $\to$ `PENDING_REVIEW` $\to$ `ACCEPTED` / `REJECTED`) ensures full traceability and scientific auditability.

---

### Rule 4: Do Not Treat Anomaly Score as Trust Score
* **Anomaly Score** $\ne$ **(100 - Trust Score)**.
* An anomaly score indicates statistical rarity: a genuine Category 5 hurricane generates an extreme anomaly score, yet its readings are authentic and highly trustworthy (high Trust Score).
* Conversely, a stuck pin or sensor drift may produce an anomaly that contradicts all neighbors, yielding a very low Trust Score.
* Every developer must treat Trust Score calculation as an evidence-weighted synthesis, never an inverted anomaly score.

---

### Rule 5: Do Not Force Uncertain Cases into a Binary Decision
* The decision engine operates on a tri-state classification:
  1. `genuine_weather`
  2. `sensor_fault`
  3. `uncertain`
* When evidence is conflicting, sparse, or statistically inconclusive, the system **must** assign `uncertain`.
* Never implement fallback heuristics that arbitrarily force borderline cases into `genuine_weather` or `sensor_fault`.

---

### Rule 6: Do Not Fabricate Model Results
* In development, testing, and mocking, never produce fake or hardcoded static values without explicit mock decorators/fixtures.
* All mocked inference data must conform to the formal data contracts defined in `docs/contracts/DATA_CONTRACTS.md`.
* Automated tests must verify actual logical pathways, edge conditions, and error states rather than tautological assertions.

---

### Rule 7: Keep ML Integration Behind an Adapter
* Backend services must never interact directly with raw ML model binaries (`.pkl`, `.onnx`, `.pt`), internal model tensors, or library-specific APIs (scikit-learn, PyTorch, TensorFlow).
* All model invocations must flow through `ml/integration/` adapters.
* If Manan updates an anomaly model from an Isolation Forest to a Graph Neural Network, only the internal adapter implementation changes—the backend service interfaces remain unchanged.

---

### Rule 8: Use Comprehensive Type Hints
* All Python functions, methods, and class attributes must include complete type annotations (`typing`, `pydantic`).
* Example:
  ```python
  def calculate_trust_score(
      anomaly_score: float,
      evidence_weights: dict[str, float],
  ) -> int:
      ...
  ```
* Avoid untyped arguments, raw `Any` where specific types are definable, and untyped dictionaries for structured data.

---

### Rule 9: Write Tests for All Critical Functionality
* Every service module, utility function, and API endpoint must have corresponding test coverage in `tests/`.
* Tests must cover:
  * Positive paths (expected nominal inputs).
  * Boundary conditions (e.g., 0% vs 100% humidity, extreme temperatures).
  * Negative / error paths (malformed payloads, missing stations, network timeouts).
* Tests must run reliably and deterministically via `pytest`.

---

### Rule 10: Every Completed Phase Must Satisfy the Five Gates
Every implementation phase in the SkyGuard AI roadmap must strictly fulfill:
1. **CODE**: Clean, robust, modular implementation adhering to architectural boundaries.
2. **DOCUMENTATION**: Updated architecture, API docs, or README reflecting the changes.
3. **TEST**: Automated unit/integration tests verifying the new behavior.
4. **VERIFICATION**: Manual or script-driven verification proving the system behaves as expected.
5. **GIT COMMIT**: Atomic commit with a conventional commit message pushed to the designated branch.

---

## 3. Git & Branching Conventions

* **Primary Development Branch for Mitali**: `mitali`
* **Commit Message Format**: Follow conventional commits:
  * `feat:` A new feature or capability.
  * `fix:` A bug fix.
  * `docs:` Documentation-only changes.
  * `refactor:` Code restructuring without changing external behavior.
  * `test:` Adding or updating tests.
  * `chore:` Build process, dependencies, or configuration changes.
* **Prohibitions**:
  * Never commit directly to `main`.
  * Never merge work to `main` without team review and approval.
  * Never force push (`git push --force`) to shared branches.
