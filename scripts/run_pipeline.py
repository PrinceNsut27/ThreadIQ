"""CLI runner script for the ThreadIQ Data Pipeline.

Executes the full pipeline:
Ingestion -> Validation -> Cleaning -> Transformation -> Database Loading.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.threadiq.data.pipeline import run_pipeline
from src.threadiq.utils.logging_config import logger


def main():
    parser = argparse.ArgumentParser(description="ThreadIQ End-to-End Data Pipeline Runner")
    parser.add_argument(
        "--mock-if-missing",
        action="store_true",
        default=False,
        help="Build and load mock demo dataset if raw files are missing from data/raw/.",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Override database connection URL (e.g. sqlite:///data/threadiq.db).",
    )
    parser.add_argument(
        "--recreate-db",
        action="store_true",
        default=False,
        help="Drop and recreate database schema before loading.",
    )
    args = parser.parse_args()

    logger.info("Initializing ThreadIQ Data Pipeline...")
    try:
        telemetry = run_pipeline(
            database_url=args.db_url,
            mock_if_missing=args.mock_if_missing,
            recreate_db=args.recreate_db,
        )
        print("\n" + "=" * 50)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 50)
        print(f"Loaded Tables:")
        for table, count in telemetry.get("loaded_tables", {}).items():
            print(f"  - {table}: {count:,} rows")
        print("=" * 50 + "\n")
    except FileNotFoundError as e:
        logger.error(f"Pipeline stopped: {e}")
        print("\n[!] Raw data files are missing. Run with --mock-if-missing to run in demo/test mode,")
        print("    or run 'python scripts/acquire_datasets.py' for download instructions.\n")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected pipeline error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
