"""Unit tests for database loading and full pipeline execution."""

from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

from src.threadiq.data.loaders import (
    create_database_schema,
    get_db_engine,
    load_dataframe_to_db,
    query_to_df,
)
from src.threadiq.data.pipeline import run_pipeline


def test_database_schema_creation_and_loading(tmp_path: Path):
    """Test schema creation and table loading in an isolated SQLite database."""
    db_file = tmp_path / "test_threadiq.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    engine = get_db_engine(db_url)

    # 1. Create tables
    create_database_schema(engine)

    # 2. Insert test customer
    cust_df = pd.DataFrame([{
        "customer_id": "c_test_01",
        "customer_unique_id": "u_test_01",
        "zip_code_prefix": "12345",
        "city": "Sao Paulo",
        "state": "SP",
        "customer_cohort": "2018-05",
        "data_source": "test",
    }])
    loaded = load_dataframe_to_db(cust_df, "dim_customers", engine=engine)
    assert loaded == 1

    # 3. Query back
    result_df = query_to_df("SELECT * FROM dim_customers WHERE customer_id = 'c_test_01'", engine=engine)
    assert len(result_df) == 1
    assert result_df.iloc[0]["city"] == "Sao Paulo"



def test_existing_sqlite_schema_gets_additive_return_source_migration(tmp_path: Path):
    """Existing databases receive the new provenance column without being dropped."""
    db_file = tmp_path / "legacy_threadiq.db"
    engine = get_db_engine(f"sqlite:///{db_file.as_posix()}")

    # Simulate a database created before return_reason_source was introduced.
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE fct_order_items ("
            "order_item_uid VARCHAR(128) PRIMARY KEY, "
            "return_reason_code VARCHAR(64), "
            "data_source VARCHAR(32) NOT NULL)"
        ))
        conn.execute(text(
            "INSERT INTO fct_order_items "
            "(order_item_uid, return_reason_code, data_source) "
            "VALUES ('legacy_1', NULL, 'olist')"
        ))

    create_database_schema(engine)

    with engine.connect() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(fct_order_items)"))
        }
        existing_row = conn.execute(text(
            "SELECT order_item_uid FROM fct_order_items WHERE order_item_uid='legacy_1'"
        )).scalar_one()

    assert "return_reason_source" in columns
    assert existing_row == "legacy_1"


def test_full_pipeline_mock_execution(tmp_path: Path):
    """Test end-to-end pipeline execution with mock data in a temporary database."""
    db_file = tmp_path / "pipeline_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    telemetry = run_pipeline(
        database_url=db_url,
        mock_if_missing=True,
    )

    assert "loaded_tables" in telemetry
    assert telemetry["loaded_tables"]["dim_customers"] > 0
    assert telemetry["loaded_tables"]["dim_products"] > 0
    assert telemetry["loaded_tables"]["fct_orders"] > 0
    assert telemetry["loaded_tables"]["fct_order_items"] > 0
    assert telemetry["loaded_tables"]["fct_shipments_deliveries"] > 0
    assert telemetry["loaded_tables"]["fct_sessions"] > 0
    assert telemetry["loaded_tables"]["fct_events_clickstream"] > 0
    assert telemetry["loaded_tables"]["fct_inventory_snapshots"] > 0

    # Verify directly via query
    engine = get_db_engine(db_url)
    orders_count = query_to_df("SELECT COUNT(*) as cnt FROM fct_orders", engine=engine).iloc[0]["cnt"]
    assert orders_count > 0
