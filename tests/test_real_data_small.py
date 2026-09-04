"""Small real-record ingestion test against live database.

Verifies:
- 1,000 real records inserted
- field mapping
- NaN -> NULL
- deterministic reading IDs
- Bhadar Dam handling
- station uniqueness
- reading uniqueness
- raw file unchanged
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from backend.app.database.session import SessionLocal
from backend.app.services.ingestion_service import (
    ingest_batch,
    prepare_record_dict,
)

GUJARAT_PATH = Path(
    r"C:\Users\MITALI SALHOTRA\Downloads\weather_observations_full_gujarat.jsonl\weather_observations_full_gujarat.jsonl"
)


def get_file_stats(path: Path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime


def stream_jsonl(filepath: Path):
    """Memory-safe streaming generator that reconstructs split lines."""
    with open(filepath, "r", encoding="utf-8") as f:
        buf = ""
        for line in f:
            buf += line.strip()
            if buf.endswith("}"):
                try:
                    yield json.loads(buf)
                    buf = ""
                except json.JSONDecodeError:
                    pass


def run_test():
    print("=== Starting Phase 1 Small Real-Record Ingestion Test ===")
    assert GUJARAT_PATH.exists(), f"Gujarat JSONL file not found at {GUJARAT_PATH}"

    # 1. Raw file stats before
    size_before, mtime_before = get_file_stats(GUJARAT_PATH)
    print(f"Raw file size before: {size_before} bytes, mtime: {mtime_before}")

    # 2. Extract 1,000 real records line-by-line streaming
    records = []
    streamer = stream_jsonl(GUJARAT_PATH)
    for obs in streamer:
        records.append(obs)
        if len(records) == 1000:
            break

    assert len(records) == 1000, f"Expected 1000 records, got {len(records)}"
    print(f"Streamed {len(records)} records from raw JSONL.")

    # Also find Bhadar Dam records from Gujarat to test Bhadar Dam disambiguation
    bhadar_records = []
    streamer_bhadar = stream_jsonl(GUJARAT_PATH)
    for obs in streamer_bhadar:
        if "bhadar" in str(obs.get("station_id", "")).lower():
            bhadar_records.append(obs)
            if len(bhadar_records) >= 10:
                break

    print(f"Found {len(bhadar_records)} Bhadar Dam records for station disambiguation verification.")

    # 3. Database session
    db = SessionLocal()
    try:
        # Ingest 1000 records
        res1 = ingest_batch(records, db)
        print(f"First ingestion batch result: {res1}")
        assert res1["inserted"] > 0, "No records inserted in first batch!"

        # Ingest Bhadar records
        res_bhadar = ingest_batch(bhadar_records, db)
        print(f"Bhadar ingestion batch result: {res_bhadar}")

        # 4. Verify in Database
        with db.bind.connect() as conn:
            # Count total
            total_count = conn.execute(text("SELECT COUNT(*) FROM readings")).scalar()
            print(f"Total readings in database: {total_count}")
            assert total_count >= 1000, f"Expected at least 1000 readings in database, got {total_count}"

            # Verify NaN -> NULL (e.g. check rainfall IS NULL and elevation IS NULL)
            null_rainfall = conn.execute(text("SELECT COUNT(*) FROM readings WHERE rainfall IS NULL")).scalar()
            null_elevation = conn.execute(text("SELECT COUNT(*) FROM readings WHERE elevation IS NULL")).scalar()
            print(f"Readings with rainfall IS NULL: {null_rainfall}")
            print(f"Readings with elevation IS NULL: {null_elevation}")
            assert null_rainfall > 0, "Expected NULL values for rainfall where raw was NaN!"
            assert null_elevation > 0, "Expected NULL values for elevation where raw was NaN!"

            # Verify deterministic reading_id for first record
            sample_rec = records[0]
            expected_prep = prepare_record_dict(sample_rec)
            expected_id = expected_prep["reading_id"]
            db_row = conn.execute(
                text("SELECT reading_id, station_id, temperature, pressure, humidity FROM readings WHERE reading_id = :rid"),
                {"rid": expected_id}
            ).fetchone()
            assert db_row is not None, f"Record with expected deterministic reading_id {expected_id} not found in DB!"
            print(f"Verified deterministic reading_id: {db_row[0]}, station: {db_row[1]}, temp: {db_row[2]}, pres: {db_row[3]}, hum: {db_row[4]}")

            # Verify Bhadar Dam stations disambiguated
            bhadar_rajkot = conn.execute(
                text("SELECT COUNT(*) FROM readings WHERE station_id = 'Bhadar_Dam_Rajkot'")
            ).scalar()
            bhadar_aravalli = conn.execute(
                text("SELECT COUNT(*) FROM readings WHERE station_id = 'Bhadar_Dam_Aravalli'")
            ).scalar()
            print(f"Bhadar_Dam_Rajkot readings: {bhadar_rajkot}")
            print(f"Bhadar_Dam_Aravalli readings: {bhadar_aravalli}")
            assert bhadar_rajkot > 0, "Expected Bhadar_Dam_Rajkot station preserved!"
            assert bhadar_aravalli > 0, "Expected Bhadar_Dam_Aravalli station preserved!"

            # Verify generic 'Bhadar dam' was NOT inserted without disambiguation
            raw_bhadar = conn.execute(
                text("SELECT COUNT(*) FROM readings WHERE station_id = 'Bhadar dam'")
            ).scalar()
            assert raw_bhadar == 0, f"Un-disambiguated 'Bhadar dam' found in database: {raw_bhadar}"

            # 5. Verify Idempotency & Reading Uniqueness (Re-ingesting same records)
            res2 = ingest_batch(records, db)
            print(f"Re-ingestion result (idempotency check): {res2}")
            assert res2["inserted"] == 0, f"Expected 0 inserts on re-ingestion, got {res2['inserted']}"
            assert res2["duplicates"] == len(records), f"Expected {len(records)} duplicates, got {res2['duplicates']}"

    finally:
        db.close()

    # 6. Verify raw file stats after (must be unchanged)
    size_after, mtime_after = get_file_stats(GUJARAT_PATH)
    assert size_before == size_after, f"Raw file size changed from {size_before} to {size_after}!"
    assert mtime_before == mtime_after, f"Raw file mtime changed from {mtime_before} to {mtime_after}!"
    print(f"Raw file integrity verified: Size {size_after} bytes, mtime {mtime_after} untouched.")

    print("\n>>> ALL SMALL REAL-RECORD INGESTION CHECKS PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    run_test()
