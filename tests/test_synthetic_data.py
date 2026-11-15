"""Unit tests for synthetic clickstream, inventory, and promotions generation."""

from pathlib import Path

import pandas as pd
import pytest

from src.threadiq.data.loaders import (
    create_database_schema,
    get_db_engine,
    load_dataframe_to_db,
    query_to_df,
)
from src.threadiq.data.synthetic import (
    SyntheticConfig,
    SyntheticDataGenerator,
)
from src.threadiq.data.validation import (
    validate_clickstream_sequences,
    validate_inventory_constraints,
    validate_promotion_constraints,
)


@pytest.fixture
def mock_dimensions():
    """Fixture providing minimal customer and product dimension frames."""
    customers = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u2", "u3"],
        "zip_code_prefix": ["01001", "02002", "03003"],
        "city": ["Sao Paulo", "Rio De Janeiro", "Belo Horizonte"],
        "state": ["SP", "RJ", "MG"],
        "customer_cohort": ["2018-05", "2018-05", "2018-05"],
        "data_source": ["olist", "olist", "olist"],
    })
    products = pd.DataFrame({
        "product_id": ["p101", "p102", "p103"],
        "fashion_style_id": ["s101", "s102", "s103"],
        "master_category": ["Apparel", "Apparel", "Footwear"],
        "sub_category": ["Topwear", "Bottomwear", "Shoes"],
        "article_type": ["T-Shirts", "Jeans", "Sneakers"],
        "base_colour": ["Black", "Blue", "White"],
        "season": ["Summer", "Fall", "All"],
        "release_year": [2018, 2018, 2018],
        "usage": ["Casual", "Casual", "Sports"],
        "product_display_name": ["Men Black T-Shirt", "Women Slim Jeans", "Running Shoes"],
        "price_reference": [39.99, 79.99, 99.99],
        "catalog_completeness_score": [100, 100, 100],
        "data_source": ["fashion_kaggle", "fashion_kaggle", "fashion_kaggle"],
    })
    orders = pd.DataFrame({
        "order_id": ["o1"],
        "customer_id": ["c1"],
        "order_status": ["delivered"],
        "purchase_timestamp": ["2018-06-15 14:30:00"],
        "approved_at": ["2018-06-15 14:35:00"],
        "estimated_delivery_date": ["2018-06-25 00:00:00"],
        "data_source": ["olist"],
    })
    items = pd.DataFrame({
        "order_id": ["o1"],
        "order_item_id": [1],
        "product_id": ["p101"],
        "price": [39.99],
        "freight_value": [10.0],
    })
    return customers, products, orders, items


def test_synthetic_reproducibility(mock_dimensions):
    """Test that identical seeds generate identical clickstream and inventory records."""
    customers, products, orders, items = mock_dimensions
    cfg = SyntheticConfig(seed=99, n_dropoff_sessions=50, inventory_days=10, n_promotions=5)

    gen1 = SyntheticDataGenerator(cfg)
    sess1, ev1, qry1 = gen1.generate_clickstream_dataset(customers, products, orders, items)
    inv1 = gen1.generate_inventory_dataset(products)
    prm1 = gen1.generate_promotions_dataset(products)

    gen2 = SyntheticDataGenerator(cfg)
    sess2, ev2, qry2 = gen2.generate_clickstream_dataset(customers, products, orders, items)
    inv2 = gen2.generate_inventory_dataset(products)
    prm2 = gen2.generate_promotions_dataset(products)

    pd.testing.assert_frame_equal(sess1, sess2)
    pd.testing.assert_frame_equal(ev1, ev2)
    pd.testing.assert_frame_equal(qry1, qry2)
    pd.testing.assert_frame_equal(inv1, inv2)
    pd.testing.assert_frame_equal(prm1, prm2)


def test_clickstream_event_sequence_validity(mock_dimensions):
    """Test that event sequences obey chronological and funnel prerequisites."""
    customers, products, orders, items = mock_dimensions
    cfg = SyntheticConfig(seed=42, n_dropoff_sessions=100)
    gen = SyntheticDataGenerator(cfg)
    sess, events, searches = gen.generate_clickstream_dataset(customers, products, orders, items)

    report = validate_clickstream_sequences(events)
    assert report.passed
    for check in report.checks:
        assert check["passed"]
        assert check["violations_count"] == 0


def test_synthetic_referential_integrity(mock_dimensions):
    """Test that customer IDs and product IDs resolve against dimension parent tables."""
    customers, products, orders, items = mock_dimensions
    cfg = SyntheticConfig(seed=42, n_dropoff_sessions=50)
    gen = SyntheticDataGenerator(cfg)
    sess, events, searches = gen.generate_clickstream_dataset(customers, products, orders, items)

    valid_cids = set(customers["customer_id"].tolist())
    valid_pids = set(products["product_id"].tolist())

    assert all(cid in valid_cids for cid in sess["customer_id"])
    assert all(cid in valid_cids for cid in events["customer_id"])

    # Product ID where populated must be valid
    populated_events = events.dropna(subset=["product_id"])
    assert all(pid in valid_pids for pid in populated_events["product_id"])


def test_inventory_constraints(mock_dimensions):
    """Test non-negative stock and quantity balance."""
    _, products, _, _ = mock_dimensions
    cfg = SyntheticConfig(seed=42, inventory_days=30)
    gen = SyntheticDataGenerator(cfg)
    inv_df = gen.generate_inventory_dataset(products)

    report = validate_inventory_constraints(inv_df)
    assert report.passed
    assert (inv_df["stock_on_hand"] >= 0).all()
    assert (inv_df["available_quantity"] >= 0).all()
    assert (inv_df["available_quantity"] <= inv_df["stock_on_hand"]).all()


def test_promotion_constraints(mock_dimensions):
    """Test valid discount range and non-inverting dates."""
    _, products, _, _ = mock_dimensions
    cfg = SyntheticConfig(seed=42, n_promotions=20)
    gen = SyntheticDataGenerator(cfg)
    promos_df = gen.generate_promotions_dataset(products)

    report = validate_promotion_constraints(promos_df)
    assert report.passed
    assert (promos_df["discount_percentage"] > 0).all()
    assert (promos_df["discount_percentage"] <= 0.70).all()
    assert (pd.to_datetime(promos_df["end_date"]) >= pd.to_datetime(promos_df["start_date"])).all()


def test_synthetic_duplicate_prevention(mock_dimensions):
    """Test that all primary keys are completely unique."""
    customers, products, orders, items = mock_dimensions
    cfg = SyntheticConfig(seed=42, n_dropoff_sessions=100, inventory_days=15, n_promotions=15)
    gen = SyntheticDataGenerator(cfg)
    sess, events, searches = gen.generate_clickstream_dataset(customers, products, orders, items)
    inv = gen.generate_inventory_dataset(products)
    promos = gen.generate_promotions_dataset(products)

    assert sess["session_id"].is_unique
    assert events["event_id"].is_unique
    assert searches["query_id"].is_unique
    assert inv["snapshot_id"].is_unique
    assert promos["promotion_id"].is_unique


def test_synthetic_database_loading(tmp_path: Path, mock_dimensions):
    """Test loading generated synthetic tables into an isolated SQLite database."""
    customers, products, orders, items = mock_dimensions
    db_file = tmp_path / "synthetic_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    engine = get_db_engine(db_url)
    create_database_schema(engine)

    # 1. Load dimensions
    load_dataframe_to_db(customers, "dim_customers", engine=engine)
    load_dataframe_to_db(products, "dim_products", engine=engine)

    # 2. Generate and load synthetic tables
    cfg = SyntheticConfig(seed=42, n_dropoff_sessions=30, inventory_days=10, n_promotions=10)
    gen = SyntheticDataGenerator(cfg)
    sess, events, searches = gen.generate_clickstream_dataset(customers, products, orders, items)
    inv = gen.generate_inventory_dataset(products)
    promos = gen.generate_promotions_dataset(products)

    load_dataframe_to_db(sess, "fct_sessions", engine=engine)
    load_dataframe_to_db(events, "fct_events_clickstream", engine=engine)
    load_dataframe_to_db(searches, "fct_search_queries", engine=engine)
    load_dataframe_to_db(inv, "fct_inventory_snapshots", engine=engine)
    load_dataframe_to_db(promos, "fct_promotions", engine=engine)

    # 3. Query back and assert
    events_cnt = query_to_df("SELECT COUNT(*) as cnt FROM fct_events_clickstream", engine=engine).iloc[0]["cnt"]
    inv_cnt = query_to_df("SELECT COUNT(*) as cnt FROM fct_inventory_snapshots", engine=engine).iloc[0]["cnt"]
    promos_cnt = query_to_df("SELECT COUNT(*) as cnt FROM fct_promotions", engine=engine).iloc[0]["cnt"]

    assert events_cnt == len(events)
    assert inv_cnt == len(inv)
    assert promos_cnt == len(promos)
