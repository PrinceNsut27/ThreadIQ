"""Data validation and quality audit module for ThreadIQ.

Performs deterministic assertions across missing values, duplicates,
timestamps, numeric domain boundaries, categorical enums, and foreign-key integrity.
"""

from typing import Any

import numpy as np
import pandas as pd

from src.threadiq.utils.logging_config import logger


class DataQualityReport:
    """Collector and formatter for data quality check results."""

    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.checks: list[dict[str, Any]] = []
        self.passed: bool = True

    def add_check(
        self,
        check_name: str,
        passed: bool,
        details: str,
        violations_count: int = 0,
        sample_violations: list[Any] | None = None,
    ) -> None:
        if not passed:
            self.passed = False
        record = {
            "dataset": self.dataset_name,
            "check": check_name,
            "passed": passed,
            "violations_count": violations_count,
            "details": details,
            "sample_violations": sample_violations or [],
        }
        self.checks.append(record)
        log_level = logger.info if passed else logger.warning
        status_tag = "[PASS]" if passed else "[FAIL]"
        log_level(f"{status_tag} {self.dataset_name}::{check_name} - {details} (violations: {violations_count})")

    def to_dataframe(self) -> pd.DataFrame:
        """Convert quality check results to a DataFrame."""
        return pd.DataFrame(self.checks)


def validate_missing_values(
    df: pd.DataFrame,
    dataset_name: str,
    mandatory_columns: list[str],
) -> tuple[pd.DataFrame, DataQualityReport]:
    """Audit missing values and assert that mandatory columns have zero nulls.

    Returns:
        tuple of (missingness_summary_df, report)
    """
    report = DataQualityReport(dataset_name)
    total_rows = len(df)

    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / max(total_rows, 1)) * 100.0

    summary_df = pd.DataFrame({
        "column": df.columns,
        "missing_count": missing_counts.values,
        "missing_pct": missing_pct.values,
        "total_rows": total_rows,
    })

    # Check mandatory columns
    for col in mandatory_columns:
        if col in df.columns:
            nulls = int(missing_counts[col])
            passed = nulls == 0
            details = f"Mandatory column '{col}' has {nulls} nulls ({missing_pct[col]:.2f}%)"
            sample = df[df[col].isnull()].index.tolist()[:5] if nulls > 0 else []
            report.add_check(
                check_name=f"mandatory_non_null_{col}",
                passed=passed,
                details=details,
                violations_count=nulls,
                sample_violations=sample,
            )

    return summary_df, report


def validate_uniqueness(
    df: pd.DataFrame,
    dataset_name: str,
    primary_keys: list[str],
) -> tuple[int, DataQualityReport]:
    """Assert uniqueness of primary key or composite key columns.

    Returns:
        tuple of (duplicate_count, report)
    """
    report = DataQualityReport(dataset_name)
    if not all(col in df.columns for col in primary_keys):
        missing = [col for col in primary_keys if col not in df.columns]
        report.add_check(
            check_name="primary_key_uniqueness",
            passed=False,
            details=f"Primary key columns not found: {missing}",
            violations_count=len(df),
        )
        return len(df), report

    dupes_mask = df.duplicated(subset=primary_keys, keep=False)
    dupe_count = int(dupes_mask.sum())
    passed = dupe_count == 0

    sample_dupes = df[dupes_mask][primary_keys].head(5).to_dict(orient="records") if dupe_count > 0 else []
    report.add_check(
        check_name=f"uniqueness_{'_'.join(primary_keys)}",
        passed=passed,
        details=f"Found {dupe_count} duplicate rows on key {primary_keys}",
        violations_count=dupe_count,
        sample_violations=sample_dupes,
    )

    return dupe_count, report


def validate_numeric_boundaries(
    df: pd.DataFrame,
    dataset_name: str,
    column: str,
    min_value: float | None = None,
    max_value: float | None = None,
    allow_null: bool = True,
) -> DataQualityReport:
    """Validate that numeric values stay within prescribed boundaries."""
    report = DataQualityReport(dataset_name)
    if column not in df.columns:
        report.add_check(
            check_name=f"numeric_bounds_{column}",
            passed=False,
            details=f"Column '{column}' not found in dataset",
            violations_count=1,
        )
        return report

    series = df[column]
    if allow_null:
        series = series.dropna()

    violations = 0
    details = f"Checked {column} range: [{min_value}, {max_value}]"

    if min_value is not None:
        min_violations = (series < min_value).sum()
        violations += int(min_violations)

    if max_value is not None:
        max_violations = (series > max_value).sum()
        violations += int(max_violations)

    passed = violations == 0
    report.add_check(
        check_name=f"numeric_bounds_{column}",
        passed=passed,
        details=f"{column} boundary check: {violations} violations out of {len(series)} values",
        violations_count=violations,
    )

    return report


def validate_timestamp_ordering(
    df: pd.DataFrame,
    dataset_name: str,
    earlier_col: str,
    later_col: str,
    allow_null: bool = True,
) -> DataQualityReport:
    """Assert that timestamps in later_col are strictly >= earlier_col."""
    report = DataQualityReport(dataset_name)
    if earlier_col not in df.columns or later_col not in df.columns:
        report.add_check(
            check_name=f"timestamp_order_{earlier_col}_vs_{later_col}",
            passed=False,
            details=f"Columns {earlier_col} or {later_col} missing",
            violations_count=1,
        )
        return report

    t_early = pd.to_datetime(df[earlier_col], errors="coerce")
    t_late = pd.to_datetime(df[later_col], errors="coerce")

    # Evaluate where both timestamps are non-null
    valid_pair = t_early.notnull() & t_late.notnull()
    inversions = valid_pair & (t_late < t_early)
    inversion_count = int(inversions.sum())

    passed = inversion_count == 0
    sample = df[inversions][[earlier_col, later_col]].head(5).to_dict(orient="records") if inversion_count > 0 else []

    report.add_check(
        check_name=f"timestamp_order_{earlier_col}_le_{later_col}",
        passed=passed,
        details=f"Found {inversion_count} chronological inversions where {later_col} < {earlier_col}",
        violations_count=inversion_count,
        sample_violations=sample,
    )

    return report


def validate_referential_integrity(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    child_fk: str,
    parent_pk: str,
    child_dataset_name: str,
    parent_dataset_name: str,
    allow_null_fk: bool = False,
) -> DataQualityReport:
    """Assert that foreign keys in child_df exist in parent_df primary keys."""
    report = DataQualityReport(child_dataset_name)

    if child_fk not in child_df.columns or parent_pk not in parent_df.columns:
        report.add_check(
            check_name=f"fk_integrity_{child_fk}_to_{parent_pk}",
            passed=False,
            details=f"Key columns missing: child {child_fk} or parent {parent_pk}",
            violations_count=1,
        )
        return report

    child_keys = child_df[child_fk]
    if allow_null_fk:
        child_keys = child_keys.dropna()

    parent_keys_set = set(parent_df[parent_pk].dropna().unique())
    orphans = child_keys[~child_keys.isin(parent_keys_set)]
    orphan_count = len(orphans)

    passed = orphan_count == 0
    sample = orphans.head(5).tolist() if orphan_count > 0 else []

    report.add_check(
        check_name=f"fk_{child_dataset_name}.{child_fk}_in_{parent_dataset_name}.{parent_pk}",
        passed=passed,
        details=f"Found {orphan_count} orphaned foreign keys ({orphan_count / max(len(child_df), 1) * 100:.2f}%)",
        violations_count=orphan_count,
        sample_violations=sample,
    )

    return report


def validate_clickstream_sequences(events_df: pd.DataFrame) -> DataQualityReport:
    """Validate user journey event sequences, timestamps, and stage dependencies within sessions."""
    report = DataQualityReport("fct_events_clickstream")
    if events_df.empty:
        report.add_check("empty_clickstream", True, "Dataset is empty, skipping sequence checks.")
        return report

    # 1. Uniqueness of event_id
    dupes = int(events_df.duplicated(subset=["event_id"]).sum())
    report.add_check(
        check_name="unique_event_ids",
        passed=(dupes == 0),
        details=f"Found {dupes} duplicate event_ids",
        violations_count=dupes,
    )

    # 2. Check within each session
    timestamp_inversions = 0
    sequence_violations = 0

    for sid, group in events_df.groupby("session_id"):
        # Check monotonic timestamps
        ts_series = pd.to_datetime(group["event_timestamp"])
        if not ts_series.is_monotonic_increasing:
            timestamp_inversions += 1

        # Check sequence rules
        event_types = group["event_type"].tolist()
        has_purchase = "purchase_completed" in event_types or "purchase" in event_types
        has_checkout = "checkout_started" in event_types or "checkout_start" in event_types
        has_cart = "add_to_cart" in event_types

        # Rule A: Purchase requires checkout
        if has_purchase and not has_checkout:
            sequence_violations += 1

        # Rule B: Checkout requires cart
        if has_checkout and not has_cart:
            sequence_violations += 1

    report.add_check(
        check_name="session_timestamp_monotonicity",
        passed=(timestamp_inversions == 0),
        details=f"Found {timestamp_inversions} sessions with inverted event timestamps",
        violations_count=timestamp_inversions,
    )
    report.add_check(
        check_name="funnel_stage_prerequisites",
        passed=(sequence_violations == 0),
        details=f"Found {sequence_violations} sessions violating prerequisite funnel steps (e.g. purchase without checkout)",
        violations_count=sequence_violations,
    )

    return report


def validate_inventory_constraints(inv_df: pd.DataFrame) -> DataQualityReport:
    """Validate inventory constraints (non-negative stock, quantity balance)."""
    report = DataQualityReport("fct_inventory_snapshots")
    if inv_df.empty:
        report.add_check("empty_inventory", True, "Dataset is empty, skipping inventory checks.")
        return report

    # Negative stock checks
    neg_soh = int((inv_df["stock_on_hand"] < 0).sum())
    report.add_check(
        check_name="non_negative_stock_on_hand",
        passed=(neg_soh == 0),
        details=f"Found {neg_soh} records with negative stock_on_hand",
        violations_count=neg_soh,
    )

    avail_col = "available_quantity" if "available_quantity" in inv_df.columns else "available_stock"
    neg_avail = int((inv_df[avail_col] < 0).sum())
    report.add_check(
        check_name="non_negative_available_quantity",
        passed=(neg_avail == 0),
        details=f"Found {neg_avail} records with negative available quantity",
        violations_count=neg_avail,
    )

    # Available cannot exceed stock on hand
    excess_avail = int((inv_df[avail_col] > inv_df["stock_on_hand"]).sum())
    report.add_check(
        check_name="available_le_stock_on_hand",
        passed=(excess_avail == 0),
        details=f"Found {excess_avail} records where available quantity exceeds stock_on_hand",
        violations_count=excess_avail,
    )

    return report


def validate_promotion_constraints(promos_df: pd.DataFrame) -> DataQualityReport:
    """Validate promotion dates and discount boundaries."""
    report = DataQualityReport("fct_promotions")
    if promos_df.empty:
        report.add_check("empty_promotions", True, "Dataset is empty, skipping promotion checks.")
        return report

    # Date check: end_date >= start_date
    t_start = pd.to_datetime(promos_df["start_date"])
    t_end = pd.to_datetime(promos_df["end_date"])
    date_inversions = int((t_end < t_start).sum())
    report.add_check(
        check_name="promotion_date_ordering",
        passed=(date_inversions == 0),
        details=f"Found {date_inversions} promotions where end_date < start_date",
        violations_count=date_inversions,
    )

    # Discount boundary: 0.0 < discount <= 0.70
    invalid_disc = int(((promos_df["discount_percentage"] <= 0.0) | (promos_df["discount_percentage"] > 0.70)).sum())
    report.add_check(
        check_name="discount_percentage_bounds",
        passed=(invalid_disc == 0),
        details=f"Found {invalid_disc} promotions with discount out of (0, 0.70] range",
        violations_count=invalid_disc,
    )

    return report
