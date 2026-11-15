"""Unit tests for CSV ingestion and telemetry."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.threadiq.data.ingestion import IngestionError, read_csv_safe


def test_read_csv_safe_success(tmp_path: Path):
    """Test standard CSV ingestion with valid UTF-8."""
    csv_file = tmp_path / "valid.csv"
    csv_file.write_text("order_id,price\nord_1,10.5\nord_2,20.0\n", encoding="utf-8")

    df, telemetry = read_csv_safe(csv_file, expected_columns=["order_id", "price"])
    assert len(df) == 2
    assert list(df.columns) == ["order_id", "price"]
    assert telemetry["rows"] == 2
    assert telemetry["encoding"] == "utf-8"


def test_read_csv_safe_encoding_fallback(tmp_path: Path):
    """Test fallback when file is encoded in latin1."""
    csv_file = tmp_path / "latin1.csv"
    content = "product_name,category\nCamisa São Paulo,Roupas\n"
    csv_file.write_bytes(content.encode("latin1"))

    df, telemetry = read_csv_safe(csv_file)
    assert len(df) == 1
    assert "São Paulo" in df.iloc[0]["product_name"]
    assert telemetry["encoding"] in ["latin1", "iso-8859-1"]


def test_read_csv_safe_missing_columns(tmp_path: Path):
    """Test that missing required columns raise an IngestionError."""
    csv_file = tmp_path / "missing_cols.csv"
    csv_file.write_text("order_id,status\nord_1,delivered\n", encoding="utf-8")

    with pytest.raises(IngestionError, match="missing 1 required columns"):
        read_csv_safe(csv_file, expected_columns=["order_id", "price"])


def test_read_csv_safe_missing_file():
    """Test that non-existent files raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_csv_safe("non_existent_file_path_12345.csv")


def test_read_csv_safe_empty_file(tmp_path: Path):
    """Test handling of empty CSV file with headers only."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("order_id,price\n", encoding="utf-8")

    df, telemetry = read_csv_safe(csv_file, expected_columns=["order_id", "price"])
    assert len(df) == 0
    assert telemetry["rows"] == 0
