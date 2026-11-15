"""Unit tests for data validation and quality audit functions."""

import pandas as pd
import pytest

from src.threadiq.data.validation import (
    validate_missing_values,
    validate_numeric_boundaries,
    validate_referential_integrity,
    validate_timestamp_ordering,
    validate_uniqueness,
)


def test_validate_missing_values_detection():
    """Test detection of nulls in mandatory columns."""
    df = pd.DataFrame({
        "order_id": ["o1", None, "o3"],
        "price": [10.0, 20.0, 30.0],
    })
    summary_df, report = validate_missing_values(df, "orders", mandatory_columns=["order_id"])
    assert not report.passed
    assert report.checks[0]["violations_count"] == 1


def test_validate_uniqueness_detection():
    """Test duplicate detection on primary key."""
    df = pd.DataFrame({
        "customer_id": ["c1", "c2", "c1"],
        "name": ["Alice", "Bob", "Alice Duplicate"],
    })
    dupes, report = validate_uniqueness(df, "customers", primary_keys=["customer_id"])
    assert dupes == 2  # Both copies of c1 flagged
    assert not report.passed


def test_validate_numeric_boundaries_negative_price():
    """Test rejection of negative prices."""
    df = pd.DataFrame({
        "item_id": [1, 2, 3],
        "price": [29.99, -5.00, 100.0],
    })
    report = validate_numeric_boundaries(df, "items", "price", min_value=0.0)
    assert not report.passed
    assert report.checks[0]["violations_count"] == 1


def test_validate_timestamp_ordering_inversion():
    """Test detection of inverted timestamps (delivery earlier than purchase)."""
    df = pd.DataFrame({
        "order_id": ["o1", "o2"],
        "purchase": ["2018-05-01 10:00:00", "2018-05-02 10:00:00"],
        "delivered": ["2018-05-05 10:00:00", "2018-05-01 10:00:00"],  # Inversion in o2
    })
    report = validate_timestamp_ordering(df, "orders", "purchase", "delivered")
    assert not report.passed
    assert report.checks[0]["violations_count"] == 1


def test_validate_referential_integrity_orphans():
    """Test detection of orphaned foreign keys."""
    orders = pd.DataFrame({"order_id": ["o1", "o2"]})
    items = pd.DataFrame({
        "order_id": ["o1", "o2", "o99_orphan"],
        "item_id": [1, 1, 1],
    })
    report = validate_referential_integrity(
        child_df=items,
        parent_df=orders,
        child_fk="order_id",
        parent_pk="order_id",
        child_dataset_name="items",
        parent_dataset_name="orders",
    )
    assert not report.passed
    assert report.checks[0]["violations_count"] == 1
    assert "o99_orphan" in report.checks[0]["sample_violations"]


def test_validate_empty_dataset():
    """Test validation on an empty dataset."""
    df = pd.DataFrame(columns=["order_id", "price"])
    summary_df, report = validate_missing_values(df, "empty_orders", mandatory_columns=["order_id"])
    assert report.passed
    assert len(summary_df) == 2
