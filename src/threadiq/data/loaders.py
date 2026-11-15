"""Database loaders and SQLAlchemy schema definitions for ThreadIQ.

Provides SQLite initialization, Table definitions with primary/foreign keys,
indexes, and bulk DataFrame loading utilities.
"""

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine

from src.threadiq.config import DATABASE_PATH, DATABASE_URL
from src.threadiq.utils.logging_config import logger

# Global metadata object
metadata = MetaData()

# 1. dim_customers
dim_customers = Table(
    "dim_customers",
    metadata,
    Column("customer_id", String(64), primary_key=True),
    Column("customer_unique_id", String(64), nullable=False, index=True),
    Column("zip_code_prefix", String(10)),
    Column("city", String(100)),
    Column("state", String(10), index=True),
    Column("customer_cohort", String(10), index=True),
    Column("data_source", String(32), nullable=False),
)

# 2. dim_products
dim_products = Table(
    "dim_products",
    metadata,
    Column("product_id", String(64), primary_key=True),
    Column("fashion_style_id", String(64), index=True),
    Column("master_category", String(64), index=True),
    Column("sub_category", String(64), index=True),
    Column("article_type", String(64), index=True),
    Column("base_colour", String(64)),
    Column("season", String(32)),
    Column("release_year", Integer),
    Column("usage", String(64)),
    Column("product_display_name", Text),
    Column("price_reference", Float),
    Column("catalog_completeness_score", Integer),
    Column("data_source", String(32), nullable=False),
)

# 3. dim_sellers
dim_sellers = Table(
    "dim_sellers",
    metadata,
    Column("seller_id", String(64), primary_key=True),
    Column("zip_code_prefix", String(10)),
    Column("city", String(100)),
    Column("state", String(10), index=True),
    Column("data_source", String(32), nullable=False),
)

# 4. fct_orders
fct_orders = Table(
    "fct_orders",
    metadata,
    Column("order_id", String(64), primary_key=True),
    Column("customer_id", String(64), ForeignKey("dim_customers.customer_id"), nullable=False, index=True),
    Column("order_status", String(32), index=True),
    Column("purchase_timestamp", DateTime, index=True),
    Column("approved_at", DateTime),
    Column("estimated_delivery_date", DateTime),
    Column("data_source", String(32), nullable=False),
)

# 5. fct_order_items
fct_order_items = Table(
    "fct_order_items",
    metadata,
    Column("order_item_uid", String(128), primary_key=True),
    Column("order_id", String(64), ForeignKey("fct_orders.order_id"), nullable=False, index=True),
    Column("order_item_id", Integer, nullable=False),
    Column("product_id", String(64), ForeignKey("dim_products.product_id"), nullable=False, index=True),
    Column("seller_id", String(64), ForeignKey("dim_sellers.seller_id"), nullable=False, index=True),
    Column("shipping_limit_date", DateTime),
    Column("price", Float, nullable=False),
    Column("freight_value", Float, nullable=False),
    Column("return_reason_code", String(64), index=True),
    Column("data_source", String(32), nullable=False),
)

# 6. fct_order_payments
fct_order_payments = Table(
    "fct_order_payments",
    metadata,
    Column("payment_uid", String(128), primary_key=True),
    Column("order_id", String(64), ForeignKey("fct_orders.order_id"), nullable=False, index=True),
    Column("payment_sequential", Integer, nullable=False),
    Column("payment_type", String(32), index=True),
    Column("payment_installments", Integer),
    Column("payment_value", Float, nullable=False),
    Column("data_source", String(32), nullable=False),
)

# 7. fct_order_reviews
fct_order_reviews = Table(
    "fct_order_reviews",
    metadata,
    Column("review_id", String(64), primary_key=True),
    Column("order_id", String(64), ForeignKey("fct_orders.order_id"), nullable=False, index=True),
    Column("review_score", Integer, nullable=False, index=True),
    Column("review_comment_title", Text),
    Column("review_comment_message", Text),
    Column("review_creation_date", DateTime),
    Column("review_answer_timestamp", DateTime),
    Column("data_source", String(32), nullable=False),
)

# 8. fct_shipments_deliveries
fct_shipments_deliveries = Table(
    "fct_shipments_deliveries",
    metadata,
    Column("shipment_id", String(128), primary_key=True),
    Column("order_id", String(64), ForeignKey("fct_orders.order_id"), nullable=False, index=True),
    Column("seller_id", String(64), ForeignKey("dim_sellers.seller_id"), nullable=False, index=True),
    Column("dispatched_at", DateTime),
    Column("delivered_customer_date", DateTime),
    Column("estimated_delivery_date", DateTime),
    Column("order_to_dispatch_hours", Integer),
    Column("dispatch_to_delivery_hours", Integer),
    Column("delivery_delay_hours", Integer),
    Column("is_late", Integer, index=True),
    Column("is_canceled", Integer, index=True),
    Column("carrier_code", String(32)),
    Column("delivery_region", String(64)),
    Column("data_source", String(32), nullable=False),
)

# 9. fct_sessions
fct_sessions = Table(
    "fct_sessions",
    metadata,
    Column("session_id", String(64), primary_key=True),
    Column("customer_id", String(64), ForeignKey("dim_customers.customer_id"), nullable=False, index=True),
    Column("session_start", DateTime, index=True),
    Column("session_end", DateTime),
    Column("device_type", String(32), index=True),
    Column("traffic_source", String(32), index=True),
    Column("converted_flag", Integer, index=True),
    Column("source_type", String(32), default="synthetic"),
    Column("data_source", String(32), nullable=False, default="synthetic"),
)

# 10. fct_events_clickstream
fct_events_clickstream = Table(
    "fct_events_clickstream",
    metadata,
    Column("event_id", String(64), primary_key=True),
    Column("session_id", String(64), ForeignKey("fct_sessions.session_id"), nullable=False, index=True),
    Column("customer_id", String(64), nullable=False, index=True),
    Column("event_timestamp", DateTime, index=True),
    Column("event_type", String(64), index=True),
    Column("product_id", String(64), ForeignKey("dim_products.product_id"), index=True, nullable=True),
    Column("category", String(64), index=True, nullable=True),
    Column("search_query", String(255), nullable=True),
    Column("device_type", String(32), index=True, nullable=True),
    Column("traffic_source", String(32), index=True, nullable=True),
    Column("price_at_event", Float, nullable=True),
    Column("source_type", String(32), default="synthetic"),
    Column("data_source", String(32), nullable=False, default="synthetic"),
)

# 11. fct_search_queries
fct_search_queries = Table(
    "fct_search_queries",
    metadata,
    Column("query_id", String(64), primary_key=True),
    Column("session_id", String(64), nullable=False, index=True),
    Column("customer_id", String(64)),
    Column("query_timestamp", DateTime, index=True),
    Column("search_term", String(255), index=True),
    Column("result_count", Integer, nullable=False),
    Column("zero_result_flag", Integer, index=True),
    Column("clicked_product_id", String(64), ForeignKey("dim_products.product_id")),
    Column("source_type", String(32), default="synthetic"),
    Column("data_source", String(32), nullable=False, default="synthetic"),
)

# 12. fct_inventory_snapshots
fct_inventory_snapshots = Table(
    "fct_inventory_snapshots",
    metadata,
    Column("snapshot_id", String(128), primary_key=True),
    Column("product_id", String(64), ForeignKey("dim_products.product_id"), nullable=False, index=True),
    Column("snapshot_date", Date, index=True),
    Column("stock_on_hand", Integer, nullable=False),
    Column("reserved_quantity", Integer, nullable=False),
    Column("available_quantity", Integer, nullable=False),
    Column("warehouse_id", String(32), index=True),
    Column("replenishment_quantity", Integer, default=0),
    Column("historical_daily_velocity", Float),
    Column("days_of_cover", Float),
    Column("stockout_flag", Integer, index=True),
    Column("replenishment_recommendation", String(64)),
    Column("source_type", String(32), default="synthetic"),
    Column("data_source", String(32), nullable=False, default="synthetic"),
)

# 13. fct_promotions
fct_promotions = Table(
    "fct_promotions",
    metadata,
    Column("promotion_id", String(64), primary_key=True),
    Column("product_id", String(64), ForeignKey("dim_products.product_id"), index=True, nullable=True),
    Column("category", String(64), index=True, nullable=True),
    Column("discount_percentage", Float, nullable=False),
    Column("start_date", Date, index=True),
    Column("end_date", Date, index=True),
    Column("promotion_type", String(64), index=True),
    Column("source_type", String(32), default="synthetic"),
    Column("data_source", String(32), nullable=False, default="synthetic"),
)

# 14. fct_experiment_assignments
fct_experiment_assignments = Table(
    "fct_experiment_assignments",
    metadata,
    Column("assignment_id", String(128), primary_key=True),
    Column("customer_id", String(64), ForeignKey("dim_customers.customer_id"), nullable=False, index=True),
    Column("experiment_id", String(64), nullable=False, index=True),
    Column("variant", String(32), nullable=False, index=True),
    Column("assigned_at", DateTime),
    Column("converted_flag", Integer),
    Column("revenue_generated", Float),
    Column("source_type", String(32), default="synthetic"),
    Column("data_source", String(32), nullable=False, default="synthetic"),
)


def get_db_engine(database_url: str | None = None) -> Engine:
    """Create and return a SQLAlchemy engine with SQLite foreign key support enabled."""
    url = database_url or DATABASE_URL
    if url.startswith("sqlite:///"):
        db_file = url.replace("sqlite:///", "")
        if db_file != ":memory:":
            Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, echo=False)

    if "sqlite" in url:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON;"))

    return engine


def create_database_schema(engine: Engine | None = None, drop_existing: bool = False) -> None:
    """Create all tables defined in metadata, optionally dropping existing tables."""
    eng = engine or get_db_engine()
    if drop_existing:
        with eng.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF;"))
            metadata.drop_all(conn)
            conn.execute(text("PRAGMA foreign_keys = ON;"))
        logger.info("Existing database schema dropped.")
    metadata.create_all(eng)
    logger.info("Database schema initialized successfully.")


def clear_database_tables(engine: Engine | None = None) -> None:
    """Safely clear all table contents in reverse dependency order."""
    eng = engine or get_db_engine()
    with eng.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF;"))
        for tbl in reversed(metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {tbl.name};"))
        conn.execute(text("PRAGMA foreign_keys = ON;"))
    logger.info("All database tables cleared successfully.")


def load_dataframe_to_db(
    df: pd.DataFrame,
    table_name: str,
    engine: Engine | None = None,
    if_exists: str = "append",
    chunksize: int = 5000,
) -> int:
    """Load a pandas DataFrame into a database table.

    Preserves DDL schemas by using DELETE instead of DROP when if_exists='replace'.

    Returns:
        Number of rows inserted.
    """
    if df.empty:
        logger.warning(f"DataFrame for table '{table_name}' is empty. 0 rows loaded.")
        return 0

    eng = engine or get_db_engine()

    if if_exists == "replace":
        with eng.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF;"))
            conn.execute(text(f"DELETE FROM {table_name};"))
            conn.execute(text("PRAGMA foreign_keys = ON;"))
        actual_if_exists = "append"
    else:
        actual_if_exists = if_exists

    df.to_sql(
        name=table_name,
        con=eng,
        if_exists=actual_if_exists,
        index=False,
        chunksize=chunksize,
        method="multi",
    )
    logger.info(f"Loaded {len(df):,} rows into '{table_name}'.")
    return len(df)


def query_to_df(
    query_str: str,
    engine: Engine | None = None,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Execute a SQL query string and return the result as a DataFrame."""
    eng = engine or get_db_engine()
    with eng.connect() as conn:
        return pd.read_sql(text(query_str), con=conn, params=params)
