"""Streaming, restartable ingestion CLI for SkyGuard AI real weather data.

Reads large raw JSONL files line-by-line without loading into RAM,
disambiguates Bhadar Dam stations, maps field aliases, converts NaN -> NULL,
computes deterministic reading IDs, and executes conflict-safe batch inserts.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database.session import SessionLocal
from backend.app.services.ingestion_service import ingest_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("skyguard.ingest_cli")


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


def run_ingestion(filepath: Path, batch_size: int = 1000, limit: int = None, state_tag: str = None):
    logger.info(f"Starting ingestion from: {filepath}")
    logger.info(f"Batch size: {batch_size}, Limit: {limit or 'ALL'}, State: {state_tag or 'Auto'}")

    if not filepath.exists():
        logger.error(f"Source file not found: {filepath}")
        return

    db = SessionLocal()
    batch = []
    total_received = 0
    total_inserted = 0
    total_duplicates = 0
    start_time = time.time()
    batch_start = time.time()
    batch_idx = 0

    try:
        for obs in stream_jsonl(filepath):
            if state_tag and not obs.get("area"):
                obs["area"] = state_tag
            batch.append(obs)
            total_received += 1

            if len(batch) >= batch_size:
                batch_idx += 1
                stats = ingest_batch(batch, db)
                total_inserted += stats["inserted"]
                total_duplicates += stats["duplicates"]
                batch_elapsed = time.time() - batch_start
                rate = len(batch) / batch_elapsed if batch_elapsed > 0 else 0
                
                if batch_idx % 10 == 0 or batch_idx == 1:
                    overall_rate = total_received / (time.time() - start_time)
                    logger.info(
                        f"Batch #{batch_idx} | Processed: {total_received:,} | "
                        f"Inserted: {total_inserted:,} | Skipped Dupes: {total_duplicates:,} | "
                        f"Rate: {rate:.1f} rec/s (Avg: {overall_rate:.1f} rec/s)"
                    )
                
                batch = []
                batch_start = time.time()

            if limit and total_received >= limit:
                logger.info(f"Reached specified limit of {limit:,} records.")
                break

        # Process any remaining records
        if batch:
            batch_idx += 1
            stats = ingest_batch(batch, db)
            total_inserted += stats["inserted"]
            total_duplicates += stats["duplicates"]
            logger.info(
                f"Final Batch #{batch_idx} | Total Processed: {total_received:,} | "
                f"Total Inserted: {total_inserted:,} | Total Dupes: {total_duplicates:,}"
            )

    except KeyboardInterrupt:
        logger.warning("Ingestion paused by user (restartable).")
    except Exception as e:
        logger.error(f"Ingestion error: {e}", exc_info=True)
    finally:
        db.close()
        total_time = time.time() - start_time
        logger.info("=== Ingestion Run Completed ===")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info(f"Total observations processed: {total_received:,}")
        logger.info(f"Total observations inserted: {total_inserted:,}")
        logger.info(f"Total duplicates skipped: {total_duplicates:,}")
        if total_time > 0:
            logger.info(f"Average throughput: {total_received / total_time:.1f} records/sec")


def main():
    parser = argparse.ArgumentParser(description="SkyGuard AI Real Data Ingestion")
    parser.add_argument("--file", type=str, required=True, help="Path to raw JSONL file")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size (default: 1000)")
    parser.add_argument("--limit", type=int, default=None, help="Maximum records to process")
    parser.add_argument("--state", type=str, default=None, help="State label (Gujarat or Maharashtra)")
    args = parser.parse_args()

    run_ingestion(
        filepath=Path(args.file),
        batch_size=args.batch_size,
        limit=args.limit,
        state_tag=args.state,
    )


if __name__ == "__main__":
    main()
