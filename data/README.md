# SkyGuard AI — Data Directory Architecture & Policy

## 1. Directory Structure

```text
data/
├── raw/                      # Immutable, original raw AWS weather telemetry
│   ├── .gitkeep
│   └── (local / external raw observations: JSONL, CSV)
├── processed/                # Reproducibly normalized datasets ready for ingest
│   ├── .gitkeep
│   └── (curated observations, feature-engineered artifacts)
├── interim/                  # Temporary staging files generated during transformation
│   └── .gitkeep
└── README.md                 # Data contracts, provenance, and storage policy
```

## 2. Core Policy: Raw Data Immutability

> **RAW DATA MUST NEVER BE MODIFIED.**

- Any file deposited into `data/raw/` is treated as read-only.
- Transformation scripts must **never** perform in-place mutation, deletion, or overwriting of raw source files.
- All transformations must follow a pure, functional ETL pattern:
  $$\text{Raw Source} \xrightarrow{\text{Read-Only}} \text{Validation \& Normalization} \xrightarrow{\text{Reproducible Script}} \text{data/processed/} \xrightarrow{\text{Batch Ingest}} \text{Supabase PostgreSQL}$$

## 3. Data Flow & Supabase Relationship

Supabase is **not** a raw file storage bucket; it is the **operational relational database** powering FastAPI backend queries, real-time alerting, and frontend dashboards:

```text
ORIGINAL RAW SOURCE (JSONL / CSV)
       │ (Read-Only)
       ▼
data/raw/ (local / cloud archive)
       │
       ▼
ETL Transformation Script (reproducible)
       │
       ▼
Data Quality Validation & Cleansing
       │
       ▼
data/processed/ (Normalized Parquet / CSV)
       │
       ▼
Batch Upsert Pipeline
       │
       ▼
Supabase PostgreSQL (`stations` & `readings`)
       │
       ▼
FastAPI Service Layer & WebSocket Stream
       │
       ▼
Frontend Dashboard & Decision Intelligence
```

## 4. Large Dataset Storage Policy

Due to Git repository limits (GitHub 100 MB hard file limit, repository quota best practices):
- **Raw observation datasets exceeding 50 MB** (such as `weather_observations_full_gujarat.jsonl` @ 513 MB and `weather_observations_full_maharashtra.jsonl` @ 739 MB) **must NOT be committed directly to Git**.
- Raw files must be stored in:
  1. **External Object Storage / Cloud Bucket** (e.g., AWS S3, Cloudflare R2, Google Cloud Storage, or Supabase Storage), or
  2. **Git LFS** (if team bandwidth and LFS storage quotas permit), or
  3. **Documented Local Raw Data Directory** with explicit download and verification instructions.
- All raw datasets tracked outside Git must have their cryptographic checksums (SHA-256) and schema contracts recorded in documentation.

## 5. How to Reproduce Processing

1. Place the verified raw JSONL / CSV files in `data/raw/`.
2. Run the ingestion/normalization script (when implemented):
   ```bash
   python -m backend.app.services.etl_processor --source data/raw/weather_observations.jsonl --target data/processed/
   ```
3. Run the validation checks:
   ```bash
   pytest tests/test_ingestion.py
   ```
4. Execute batch ingestion to Supabase:
   ```bash
   python -m backend.app.services.supabase_loader --batch-size 1000
   ```
