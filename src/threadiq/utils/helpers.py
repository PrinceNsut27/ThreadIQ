"""General helper functions for ThreadIQ."""

import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from src.threadiq.utils.logging_config import logger


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def safe_divide(numerator: float | int, denominator: float | int, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default on zero or null denominator."""
    if denominator is None or denominator == 0 or (isinstance(denominator, float) and abs(denominator) < 1e-9):
        return default
    if numerator is None:
        return default
    return float(numerator) / float(denominator)


@contextmanager
def execution_timer(task_name: str):
    """Context manager for timing task execution and logging duration."""
    start_time = time.perf_counter()
    logger.info(f"Started: {task_name}")
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        logger.info(f"Finished: {task_name} in {elapsed:.3f}s")
