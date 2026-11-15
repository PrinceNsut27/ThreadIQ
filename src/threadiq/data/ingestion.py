"""Data ingestion module for ThreadIQ.

Provides robust, read-only CSV loading with multi-encoding fallback,
schema pre-validation, bad-line handling, and detailed ingestion telemetry.
"""

import time
from pathlib import Path
from typing import Any

import pandas as pd

from src.threadiq.config import (
    FASHION_FILES,
    FASHION_RAW_DIR,
    OLIST_FILES,
    OLIST_RAW_DIR,
    RAW_SCHEMAS,
)
from src.threadiq.utils.helpers import format_bytes
from src.threadiq.utils.logging_config import logger


class IngestionError(Exception):
    """Custom exception raised when data ingestion fails."""
    pass


def read_csv_safe(
    file_path: Path | str,
    expected_columns: list[str] | None = None,
    encodings: tuple[str, ...] = ("utf-8", "latin1", "iso-8859-1", "cp1252"),
    on_bad_lines: str = "skip",
    **kwargs: Any,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read a CSV file safely with multi-encoding fallback, schema check, and telemetry.

    Args:
        file_path: Path to the target CSV file.
        expected_columns: Optional list of required column names.
        encodings: Tuple of encodings to attempt in priority order.
        on_bad_lines: Strategy for malformed lines ('skip', 'error', 'warn').
        **kwargs: Additional keyword arguments passed to pd.read_csv.

    Returns:
        tuple of (pd.DataFrame, telemetry_dict)

    Raises:
        FileNotFoundError: If the file does not exist.
        IngestionError: If file cannot be decoded or lacks required columns.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Source file not found at: {path}")

    file_size_bytes = path.stat().st_size
    df: pd.DataFrame | None = None
    successful_encoding: str | None = None
    last_exception: Exception | None = None

    start_time = time.perf_counter()

    for enc in encodings:
        try:
            # Strictly read-only operation
            df = pd.read_csv(path, encoding=enc, on_bad_lines=on_bad_lines, **kwargs)
            successful_encoding = enc
            break
        except UnicodeDecodeError as e:
            last_exception = e
            logger.debug(f"Encoding {enc} failed for {path.name}: {e}. Retrying with next encoding.")
            continue
        except Exception as e:
            last_exception = e
            break

    if df is None:
        raise IngestionError(
            f"Failed to ingest CSV '{path.name}' across attempted encodings {encodings}. "
            f"Root cause: {last_exception}"
        )

    # Validate required columns if specified
    if expected_columns:
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols:
            raise IngestionError(
                f"File '{path.name}' is missing {len(missing_cols)} required columns: {missing_cols}"
            )

    elapsed_sec = time.perf_counter() - start_time
    mem_bytes = int(df.memory_usage(deep=True).sum())

    telemetry = {
        "file_name": path.name,
        "file_path": str(path),
        "file_size": format_bytes(file_size_bytes),
        "file_size_bytes": file_size_bytes,
        "encoding": successful_encoding,
        "rows": len(df),
        "columns": len(df.columns),
        "memory_usage": format_bytes(mem_bytes),
        "memory_bytes": mem_bytes,
        "elapsed_sec": round(elapsed_sec, 4),
    }

    logger.info(
        f"Ingested {path.name}: {telemetry['rows']:,} rows, "
        f"{telemetry['columns']} cols, {telemetry['memory_usage']} in {elapsed_sec:.3f}s "
        f"({successful_encoding})"
    )

    return df, telemetry


def ingest_raw_olist(olist_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Ingest all 9 Olist CSV datasets from raw directory.

    Returns:
        Dictionary mapping table name to DataFrame.
    """
    target_dir = olist_dir or OLIST_RAW_DIR
    if not target_dir.exists():
        raise FileNotFoundError(f"Olist raw directory does not exist: {target_dir}")

    datasets: dict[str, pd.DataFrame] = {}

    for file_name in OLIST_FILES:
        table_key = file_name.replace(".csv", "")
        file_path = target_dir / file_name
        expected_cols = RAW_SCHEMAS.get(table_key)
        
        df, _ = read_csv_safe(
            file_path=file_path,
            expected_columns=expected_cols,
            encodings=("utf-8", "latin1"),
        )
        datasets[table_key] = df

    return datasets


def ingest_raw_fashion(fashion_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Ingest Fashion Product styles metadata from raw directory.

    Returns:
        Dictionary mapping 'styles' to DataFrame.
    """
    target_dir = fashion_dir or FASHION_RAW_DIR
    if not target_dir.exists():
        raise FileNotFoundError(f"Fashion raw directory does not exist: {target_dir}")

    styles_path = target_dir / "styles.csv"
    expected_cols = RAW_SCHEMAS.get("styles")

    # styles.csv has known unquoted commas in product names, hence on_bad_lines='skip'
    df, _ = read_csv_safe(
        file_path=styles_path,
        expected_columns=expected_cols,
        encodings=("utf-8", "latin1"),
        on_bad_lines="skip",
    )

    return {"styles": df}
