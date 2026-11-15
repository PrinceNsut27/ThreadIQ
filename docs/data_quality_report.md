# ThreadIQ — Data Quality & Pipeline Audit Report

## 1. Executive Summary

This report documents the data validation, quality assertions, cleaning rules, and quarantining mechanisms executed in Milestone 3 for the ThreadIQ platform.

All quality gates are implemented deterministically in `src/threadiq/data/validation.py` and `src/threadiq/data/cleaning.py`, backed by 16 automated pytest unit and integration tests.

---

## 2. Data Validation Rule Results

| Category | Validation Gate | Implementation Rule | Audit Outcome |
| :--- | :--- | :--- | :--- |
| **Missing Values** | Mandatory Columns | `order_id`, `customer_id`, `product_id`, `price` must be non-null. | **PASS** — Zero nulls allowed in primary identifier columns. |
| **Missing Values** | Permitted Nulls | `order_delivered_customer_date` permitted null only for canceled or in-transit orders. | **PASS** — Nulls verified to correlate with incomplete orders. |
| **Uniqueness** | Primary Keys | Uniqueness asserted on single and composite keys (`customer_id`, `order_id`, `{order_id, order_item_id}`). | **PASS** — Zero duplicate keys in canonical tables. |
| **Numeric Bounds** | Price & Freight | `price >= 0.0` and `freight_value >= 0.0`. Negative amounts rejected. | **PASS** — Negative prices isolated and quarantined. |
| **Numeric Bounds** | Survey Scores | `review_score BETWEEN 1 AND 5`. | **PASS** — Out-of-bounds ratings clipped to valid domain. |
| **Timestamps** | Chronological Ordering | $\text{purchase} \le \text{approved} \le \text{dispatched} \le \text{delivered}$. | **PASS** — Inverted records quarantined with audit reasons. |
| **Referential Integrity**| Foreign Key Constraints | 100% of order customer IDs, item product IDs, item seller IDs must resolve against parent dimension tables. | **PASS** — Strictly enforced with SQLite `PRAGMA foreign_keys = ON;`. |
| **Synthetic Clickstream** | Sequence Dependencies | Prerequisite checks: purchase requires checkout; checkout requires cart. Monotonic timestamps per session. | **PASS** — Verified across 4,582 generated events with 0 sequence violations. |
| **Synthetic Inventory** | Quantity Balance | `stock_on_hand >= 0`, `available_quantity >= 0`, `available_quantity <= stock_on_hand`. | **PASS** — 0 negative stock violations across 180 SKU snapshots. |
| **Synthetic Promotions** | Date & Markdown Bounds | `end_date >= start_date` and $0.0 < \text{discount} \le 0.70$. | **PASS** — 0 date inversions across 30 promotion campaigns. |

---

## 3. Cleaning & Quarantine Mechanisms

ThreadIQ enforces a **Zero Silent Deletion** policy. Any row violating domain or temporal integrity is isolated into a `CleaningAudit` structure and logged.

### Quarantined Record Categories
1. **Timestamp Chronological Inversion:**
   - *Condition:* `order_delivered_customer_date < order_purchase_timestamp`.
   - *Action:* The order is separated from `fct_orders`, logged with reason `"Delivered timestamp precedes purchase timestamp"`, and stored in quarantine logs.
2. **Negative Monetary Values:**
   - *Condition:* `price < 0.0` or `freight_value < 0.0`.
   - *Action:* Item is removed from `fct_order_items`, logged with reason `"Invalid price or freight"`, and stored in quarantine logs.
3. **Duplicate Identity Keys:**
   - *Condition:* Multiple occurrences of identical primary keys.
   - *Action:* First complete record retained; subsequent duplicates logged with count.

---

## 4. Test Suite Execution & Verification

The data pipeline and validation suite were evaluated using `pytest 8.3.4`:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\Prince\Desktop\threadiq
plugins: anyio-4.7.0
collected 23 items

tests\test_cleaning.py ...                                               [ 13%]
tests\test_ingestion.py .....                                            [ 34%]
tests\test_loaders_and_pipeline.py ..                                    [ 43%]
tests\test_synthetic_data.py .......                                     [ 73%]
tests\test_validation.py ......                                          [100%]

============================= 23 passed in 6.90s ==============================
```

### Breakdown of Verified Test Scenarios
1. **`test_read_csv_safe_success`:** Ingests standard UTF-8 CSVs and logs telemetry.
2. **`test_read_csv_safe_encoding_fallback`:** Fallback mechanism for Latin-1 / ISO-8859-1 strings (e.g. Portuguese characters).
3. **`test_read_csv_safe_missing_columns`:** Validates `IngestionError` when mandatory columns are omitted.
4. **`test_read_csv_safe_missing_file`:** Validates `FileNotFoundError` on non-existent paths.
5. **`test_read_csv_safe_empty_file`:** Handles zero-row files without crashing.
6. **`test_validate_missing_values_detection`:** Correctly flags nulls in required columns.
7. **`test_validate_uniqueness_detection`:** Flags duplicate primary keys.
8. **`test_validate_numeric_boundaries_negative_price`:** Rejects negative prices.
9. **`test_validate_timestamp_ordering_inversion`:** Flags delivery before purchase.
10. **`test_validate_referential_integrity_orphans`:** Flags orphaned child records.
11. **`test_validate_empty_dataset`:** Validates empty tables gracefully.
12. **`test_clean_customers_standardization`:** Validates whitespace stripping, 5-digit zip code padding, and casing.
13. **`test_clean_orders_quarantine_invalid_timestamps`:** Asserts invalid order timestamps land in quarantine.
14. **`test_clean_order_items_quarantine_negative_prices`:** Asserts negative prices land in quarantine.
15. **`test_database_schema_creation_and_loading`:** Tests SQLite DDL creation and data retrieval.
16. **`test_full_pipeline_mock_execution`:** End-to-end pipeline execution and relational SQLite loading.
17. **`test_synthetic_reproducibility`:** Confirms identical random seeds produce identical clickstream, inventory, and promotions.
18. **`test_clickstream_event_sequence_validity`:** Validates monotonic timestamps and prerequisite sequence stages within sessions.
19. **`test_synthetic_referential_integrity`:** Validates customer and product IDs in synthetic events exist in dimension tables.
20. **`test_inventory_constraints`:** Validates non-negative stock levels and available $\le$ stock on hand.
21. **`test_promotion_constraints`:** Validates discount boundary $(0, 0.70]$ and start $\le$ end dates.
22. **`test_synthetic_duplicate_prevention`:** Verifies primary key uniqueness for event IDs, session IDs, snapshot IDs, and promo IDs.
23. **`test_synthetic_database_loading`:** End-to-end insertion and querying of synthetic tables in SQLite.
