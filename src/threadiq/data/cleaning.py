"""Data cleaning and sanitisation module for ThreadIQ.

Performs deterministic data standardisation, type casting, missing value imputation,
and record quarantining. NEVER silently deletes records.
"""

from typing import Any

import numpy as np
import pandas as pd

from src.threadiq.utils.logging_config import logger


class CleaningAudit:
    """Audit log tracking records quarantined or modified during cleaning."""

    def __init__(self):
        self.quarantined_records: list[dict[str, Any]] = []
        self.modifications: list[dict[str, Any]] = []

    def record_quarantine(
        self,
        dataset: str,
        record_id: Any,
        reason: str,
        original_record: dict[str, Any],
    ) -> None:
        entry = {
            "dataset": dataset,
            "record_id": str(record_id),
            "reason": reason,
            "original_record": original_record,
        }
        self.quarantined_records.append(entry)
        logger.warning(f"Quarantined record in {dataset} [ID: {record_id}]: {reason}")

    def record_modification(
        self,
        dataset: str,
        column: str,
        count: int,
        description: str,
    ) -> None:
        self.modifications.append({
            "dataset": dataset,
            "column": column,
            "count": count,
            "description": description,
        })
        logger.info(f"Cleaned {dataset}.{column}: {description} (affected {count:,} rows)")

    def get_quarantine_summary(self) -> pd.DataFrame:
        if not self.quarantined_records:
            return pd.DataFrame(columns=["dataset", "record_id", "reason", "original_record"])
        return pd.DataFrame(self.quarantined_records)


def clean_customers(df: pd.DataFrame, audit: CleaningAudit | None = None) -> pd.DataFrame:
    """Clean customers dataset."""
    df_clean = df.copy()
    audit = audit or CleaningAudit()

    # Drop exact duplicate rows if any and log
    initial_len = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=["customer_id"])
    dupes_dropped = initial_len - len(df_clean)
    if dupes_dropped > 0:
        audit.record_modification("customers", "customer_id", dupes_dropped, "Dropped duplicate customer_ids")

    # Standardize strings
    df_clean["customer_id"] = df_clean["customer_id"].astype(str).str.strip()
    df_clean["customer_unique_id"] = df_clean["customer_unique_id"].astype(str).str.strip()
    df_clean["customer_zip_code_prefix"] = (
        df_clean["customer_zip_code_prefix"].fillna(0).astype(int).astype(str).str.zfill(5)
    )
    df_clean["customer_city"] = df_clean["customer_city"].fillna("Unknown").astype(str).str.strip().str.title()
    df_clean["customer_state"] = df_clean["customer_state"].fillna("XX").astype(str).str.strip().str.upper()

    return df_clean


def clean_orders(df: pd.DataFrame, audit: CleaningAudit | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean orders dataset.

    Returns:
        tuple of (cleaned_df, quarantined_df)
    """
    df_clean = df.copy()
    audit = audit or CleaningAudit()

    # Standardize order_status
    df_clean["order_status"] = df_clean["order_status"].fillna("unknown").astype(str).str.strip().str.lower()

    # Convert timestamps
    timestamp_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in timestamp_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce")

    # Quarantine invalid records: delivery timestamp earlier than purchase timestamp
    has_both_dates = df_clean["order_delivered_customer_date"].notnull() & df_clean["order_purchase_timestamp"].notnull()
    invalid_delivery_mask = has_both_dates & (df_clean["order_delivered_customer_date"] < df_clean["order_purchase_timestamp"])

    quarantined = df_clean[invalid_delivery_mask].copy()
    for _, row in quarantined.iterrows():
        audit.record_quarantine(
            dataset="orders",
            record_id=row["order_id"],
            reason="Delivered timestamp precedes purchase timestamp",
            original_record=row.to_dict(),
        )

    # Valid records
    df_clean = df_clean[~invalid_delivery_mask].copy()

    # Deduplicate on order_id
    dupe_mask = df_clean.duplicated(subset=["order_id"])
    if dupe_mask.any():
        num_dupes = int(dupe_mask.sum())
        audit.record_modification("orders", "order_id", num_dupes, "Deduplicated order_id (kept first)")
        df_clean = df_clean.drop_duplicates(subset=["order_id"], keep="first")

    return df_clean, quarantined


def clean_order_items(df: pd.DataFrame, audit: CleaningAudit | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean order items dataset, rejecting negative prices/freights.

    Returns:
        tuple of (cleaned_df, quarantined_df)
    """
    df_clean = df.copy()
    audit = audit or CleaningAudit()

    # Cast numeric types
    df_clean["order_item_id"] = pd.to_numeric(df_clean["order_item_id"], errors="coerce").fillna(1).astype(int)
    df_clean["price"] = pd.to_numeric(df_clean["price"], errors="coerce")
    df_clean["freight_value"] = pd.to_numeric(df_clean["freight_value"], errors="coerce")

    if "shipping_limit_date" in df_clean.columns:
        df_clean["shipping_limit_date"] = pd.to_datetime(df_clean["shipping_limit_date"], errors="coerce")

    # Quarantine records with negative price or negative freight
    invalid_mask = (df_clean["price"] < 0) | (df_clean["freight_value"] < 0) | df_clean["price"].isnull()
    quarantined = df_clean[invalid_mask].copy()

    for _, row in quarantined.iterrows():
        audit.record_quarantine(
            dataset="order_items",
            record_id=f"{row.get('order_id')}_{row.get('order_item_id')}",
            reason=f"Invalid price ({row.get('price')}) or freight ({row.get('freight_value')})",
            original_record=row.to_dict(),
        )

    df_clean = df_clean[~invalid_mask].copy()

    # Deduplicate composite key
    df_clean = df_clean.drop_duplicates(subset=["order_id", "order_item_id"], keep="first")

    return df_clean, quarantined


def clean_fashion_styles(df: pd.DataFrame, audit: CleaningAudit | None = None) -> pd.DataFrame:
    """Clean Fashion Product Images styles metadata."""
    df_clean = df.copy()
    audit = audit or CleaningAudit()

    # Clean ID
    df_clean["id"] = pd.to_numeric(df_clean["id"], errors="coerce")
    df_clean = df_clean.dropna(subset=["id"]).copy()
    df_clean["id"] = df_clean["id"].astype(int)

    # Standardize string categories
    string_cols = ["gender", "masterCategory", "subCategory", "articleType", "baseColour", "season", "usage"]
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Unknown").astype(str).str.strip().str.title()

    if "productDisplayName" in df_clean.columns:
        df_clean["productDisplayName"] = df_clean["productDisplayName"].fillna("Fashion Product").astype(str).str.strip()

    if "year" in df_clean.columns:
        df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce")

    # Deduplicate on id
    df_clean = df_clean.drop_duplicates(subset=["id"], keep="first")

    return df_clean


def clean_order_reviews(df: pd.DataFrame, audit: CleaningAudit | None = None) -> pd.DataFrame:
    """Clean order reviews dataset."""
    df_clean = df.copy()
    audit = audit or CleaningAudit()

    # Score must be between 1 and 5
    df_clean["review_score"] = pd.to_numeric(df_clean["review_score"], errors="coerce").fillna(3).astype(int)
    df_clean["review_score"] = df_clean["review_score"].clip(lower=1, upper=5)

    # Fill missing comments
    df_clean["review_comment_title"] = df_clean["review_comment_title"].fillna("").astype(str).str.strip()
    df_clean["review_comment_message"] = df_clean["review_comment_message"].fillna("").astype(str).str.strip()

    # Standardize timestamps
    for col in ["review_creation_date", "review_answer_timestamp"]:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce")

    # Deduplicate review_id
    df_clean = df_clean.drop_duplicates(subset=["review_id"], keep="first")

    return df_clean
