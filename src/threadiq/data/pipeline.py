"""End-to-end data pipeline orchestrator for ThreadIQ.

Executes:
Raw Ingestion -> Schema Validation -> Quality Cleaning & Quarantine ->
Canonical Transformation & Synthetic Generation -> Validation -> SQLite Database Loading.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

from src.threadiq.config import (
    DATABASE_URL,
    FASHION_RAW_DIR,
    OLIST_RAW_DIR,
    RANDOM_SEED,
)
from src.threadiq.data.cleaning import (
    CleaningAudit,
    clean_customers,
    clean_fashion_styles,
    clean_order_items,
    clean_order_reviews,
    clean_orders,
)
from src.threadiq.data.ingestion import (
    IngestionError,
    ingest_raw_fashion,
    ingest_raw_olist,
)
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
from src.threadiq.data.transformations import (
    build_dim_customers,
    build_dim_products,
    build_dim_sellers,
    build_fct_order_items,
    build_fct_order_payments,
    build_fct_order_reviews,
    build_fct_orders,
    build_fct_shipments_deliveries,
)
from src.threadiq.data.validation import (
    validate_clickstream_sequences,
    validate_inventory_constraints,
    validate_missing_values,
    validate_numeric_boundaries,
    validate_promotion_constraints,
    validate_referential_integrity,
    validate_timestamp_ordering,
    validate_uniqueness,
)
from src.threadiq.utils.helpers import execution_timer
from src.threadiq.utils.logging_config import logger


def run_pipeline(
    olist_dir: Path | None = None,
    fashion_dir: Path | None = None,
    database_url: str | None = None,
    mock_if_missing: bool = False,
    recreate_db: bool = False,
    synthetic_config: SyntheticConfig | None = None,
) -> dict[str, Any]:
    """Execute the full data pipeline.

    Args:
        olist_dir: Optional override for Olist raw data directory.
        fashion_dir: Optional override for Fashion raw data directory.
        database_url: Optional override for database connection URL.
        mock_if_missing: If True and raw files are absent, builds a synthetic demo dataset.
        recreate_db: If True, drops and recreates schema before loading.
        synthetic_config: Optional custom SyntheticConfig.

    Returns:
        Telemetry summary dictionary.
    """
    with execution_timer("ThreadIQ Data Pipeline Execution"):
        target_olist = olist_dir or OLIST_RAW_DIR
        target_fashion = fashion_dir or FASHION_RAW_DIR
        db_url = database_url or DATABASE_URL
        synth_cfg = synthetic_config or SyntheticConfig(seed=RANDOM_SEED)

        audit = CleaningAudit()
        telemetry: dict[str, Any] = {"stages": {}, "loaded_tables": {}}

        # Stage 1: Ingestion
        logger.info("--- Stage 1: Ingestion ---")
        raw_olist: dict[str, pd.DataFrame] = {}
        raw_fashion: dict[str, pd.DataFrame] = {}

        try:
            raw_olist = ingest_raw_olist(target_olist)
            telemetry["stages"]["ingest_olist"] = "SUCCESS"
        except FileNotFoundError as e:
            logger.warning(f"Olist raw files not found: {e}")
            telemetry["stages"]["ingest_olist"] = "MISSING_RAW_FILES"
            if not mock_if_missing:
                raise

        try:
            raw_fashion = ingest_raw_fashion(target_fashion)
            telemetry["stages"]["ingest_fashion"] = "SUCCESS"
        except FileNotFoundError as e:
            logger.warning(f"Fashion raw files not found: {e}")
            telemetry["stages"]["ingest_fashion"] = "MISSING_RAW_FILES"
            if not mock_if_missing:
                raise

        if mock_if_missing and (not raw_olist or not raw_fashion):
            logger.info("Constructing rich mock dataset for testing & verification...")
            raw_olist, raw_fashion = _create_mock_raw_tables()

        # Stage 2: Validation of Ingested Inputs
        logger.info("--- Stage 2: Validation of Ingested Inputs ---")
        validate_missing_values(raw_olist["olist_orders_dataset"], "orders", ["order_id", "customer_id", "order_status"])
        validate_uniqueness(raw_olist["olist_orders_dataset"], "orders", ["order_id"])
        validate_numeric_boundaries(raw_olist["olist_order_items_dataset"], "order_items", "price", min_value=0.0)
        validate_timestamp_ordering(raw_olist["olist_orders_dataset"], "orders", "order_purchase_timestamp", "order_delivered_customer_date")

        # Stage 3: Cleaning & Quarantine
        logger.info("--- Stage 3: Cleaning & Quarantining ---")
        clean_cust_df = clean_customers(raw_olist["olist_customers_dataset"], audit=audit)
        clean_ord_df, quar_orders = clean_orders(raw_olist["olist_orders_dataset"], audit=audit)
        clean_items_df, quar_items = clean_order_items(raw_olist["olist_order_items_dataset"], audit=audit)
        clean_styles_df = clean_fashion_styles(raw_fashion["styles"], audit=audit)
        clean_reviews_df = clean_order_reviews(raw_olist["olist_order_reviews_dataset"], audit=audit)

        telemetry["quarantine_summary"] = {
            "quarantined_orders": len(quar_orders),
            "quarantined_items": len(quar_items),
        }

        # Stage 4: Transformations
        logger.info("--- Stage 4: Transformation to Canonical Schema ---")
        dim_cust = build_dim_customers(clean_cust_df, clean_ord_df)
        dim_sell = build_dim_sellers(raw_olist["olist_sellers_dataset"])
        dim_prod = build_dim_products(styles_df=clean_styles_df)
        fct_ord = build_fct_orders(clean_ord_df)
        fct_items = build_fct_order_items(clean_items_df, orders_df=clean_ord_df, reviews_df=clean_reviews_df)
        fct_payments = build_fct_order_payments(raw_olist["olist_order_payments_dataset"])
        fct_reviews = build_fct_order_reviews(clean_reviews_df)
        fct_shipments = build_fct_shipments_deliveries(clean_ord_df, clean_items_df)

        # Stage 5: Synthetic Simulation
        logger.info("--- Stage 5: Realistic Synthetic Behavioural & Operational Generation ---")
        synth_generator = SyntheticDataGenerator(synth_cfg)
        fct_sess, fct_events, fct_searches = synth_generator.generate_clickstream_dataset(
            customers_df=dim_cust,
            products_df=dim_prod,
            orders_df=fct_ord,
            items_df=fct_items,
        )
        fct_inv = synth_generator.generate_inventory_dataset(dim_prod)
        fct_promos = synth_generator.generate_promotions_dataset(dim_prod)

        # Validate generated synthetic records
        validate_clickstream_sequences(fct_events)
        validate_inventory_constraints(fct_inv)
        validate_promotion_constraints(fct_promos)

        # Stage 6: Database Loading
        logger.info(f"--- Stage 6: Database Loading ({db_url}) ---")
        engine = get_db_engine(db_url)
        create_database_schema(engine, drop_existing=recreate_db)

        tables_to_load = [
            ("dim_customers", dim_cust),
            ("dim_sellers", dim_sell),
            ("dim_products", dim_prod),
            ("fct_orders", fct_ord),
            ("fct_order_items", fct_items),
            ("fct_order_payments", fct_payments),
            ("fct_order_reviews", fct_reviews),
            ("fct_shipments_deliveries", fct_shipments),
            ("fct_sessions", fct_sess),
            ("fct_events_clickstream", fct_events),
            ("fct_search_queries", fct_searches),
            ("fct_inventory_snapshots", fct_inv),
            ("fct_promotions", fct_promos),
        ]

        for table_name, df_data in tables_to_load:
            loaded_count = load_dataframe_to_db(df_data, table_name, engine=engine, if_exists="replace")
            telemetry["loaded_tables"][table_name] = loaded_count

        logger.info("Data Pipeline executed successfully.")
        return telemetry


def _create_mock_raw_tables() -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """Generate realistic mock raw tables with rich distributions for analytics verification."""
    rng = np.random.default_rng(RANDOM_SEED)

    # 1. 50 Customers with 35 unique IDs (15 repeat customers)
    n_cust = 50
    unique_ids = [f"u_{i:03d}" for i in range(1, 36)]
    cust_records = []
    cities_states = [("Sao Paulo", "SP"), ("Rio De Janeiro", "RJ"), ("Belo Horizonte", "MG"), ("Curitiba", "PR"), ("Porto Alegre", "RS")]

    for i in range(1, n_cust + 1):
        uid = rng.choice(unique_ids)
        c_city, c_state = cities_states[int(rng.integers(0, len(cities_states)))]
        cust_records.append({
            "customer_id": f"cust_{i:03d}",
            "customer_unique_id": uid,
            "customer_zip_code_prefix": int(rng.integers(10000, 99999)),
            "customer_city": c_city,
            "customer_state": c_state,
        })
    olist_customers = pd.DataFrame(cust_records)

    # 2. 20 Products across fashion categories
    product_specs = [
        (1101, "Men", "Apparel", "Topwear", "T-Shirts", "Black", "Summer", 2018, "Casual", "Men Slim Black T-Shirt", 39.99),
        (1102, "Men", "Apparel", "Topwear", "Shirts", "White", "All", 2018, "Formal", "Men Formal White Shirt", 89.90),
        (1103, "Women", "Apparel", "Bottomwear", "Jeans", "Blue", "Fall", 2018, "Casual", "Women High-Rise Skinny Jeans", 129.50),
        (1104, "Women", "Apparel", "Topwear", "Tops", "Red", "Summer", 2018, "Casual", "Women Floral Summer Top", 49.99),
        (1105, "Unisex", "Footwear", "Shoes", "Sneakers", "White", "All", 2018, "Sports", "Unisex Running Classic Sneakers", 159.90),
        (1106, "Men", "Footwear", "Shoes", "Formal Shoes", "Brown", "All", 2018, "Formal", "Men Leather Oxford Shoes", 199.90),
        (1107, "Women", "Footwear", "Shoes", "Heels", "Black", "All", 2018, "Party", "Women Stiletto Party Heels", 149.00),
        (1108, "Women", "Apparel", "Dress", "Dresses", "Navy Blue", "Summer", 2018, "Casual", "Women Casual Shift Dress", 89.90),
        (1109, "Men", "Apparel", "Bottomwear", "Trousers", "Grey", "All", 2018, "Formal", "Men Slim Fit Chino Trousers", 99.50),
        (1110, "Unisex", "Accessories", "Bags", "Backpacks", "Black", "All", 2018, "Casual", "Urban Laptop Backpack", 119.00),
        (1111, "Women", "Accessories", "Bags", "Handbags", "Tan", "All", 2018, "Casual", "Women Structured Tote Bag", 139.90),
        (1112, "Men", "Apparel", "Topwear", "Sweaters", "Navy Blue", "Winter", 2018, "Casual", "Men Knit Crewneck Sweater", 109.90),
        (1113, "Women", "Apparel", "Topwear", "Jackets", "Black", "Winter", 2018, "Casual", "Women Quilted Winter Jacket", 189.90),
        (1114, "Men", "Apparel", "Bottomwear", "Shorts", "Khaki", "Summer", 2018, "Casual", "Men Cotton Cargo Shorts", 45.00),
        (1115, "Women", "Apparel", "Bottomwear", "Skirts", "Black", "Summer", 2018, "Casual", "Women Pleated A-Line Skirt", 59.90),
        (1116, "Unisex", "Accessories", "Eyewear", "Sunglasses", "Black", "All", 2018, "Casual", "Polarized Aviator Sunglasses", 79.90),
        (1117, "Men", "Apparel", "Topwear", "Polo T-Shirts", "Green", "Summer", 2018, "Casual", "Men Pique Cotton Polo", 55.00),
        (1118, "Women", "Footwear", "Flats", "Ballerinas", "Beige", "All", 2018, "Casual", "Women Comfort Ballet Flats", 69.90),
        (1119, "Men", "Apparel", "Activewear", "Track Pants", "Grey", "All", 2018, "Sports", "Men Gym Training Trackpants", 65.00),
        (1120, "Women", "Apparel", "Activewear", "Leggings", "Black", "All", 2018, "Sports", "Women High-Waist Yoga Leggings", 59.90),
    ]

    styles_records = []
    for spec in product_specs:
        pid, g, mc, sc, at, col, s, y, u, name, pr = spec
        # Introduce a few realistic missing attributes for testing data quality
        usage_val = None if pid in [1104, 1115] else u
        season_val = None if pid in [1102, 1111] else s
        styles_records.append({
            "id": pid, "gender": g, "masterCategory": mc, "subCategory": sc,
            "articleType": at, "baseColour": col, "season": season_val, "year": y,
            "usage": usage_val, "productDisplayName": name,
        })
    styles = pd.DataFrame(styles_records)

    # 3. 4 Sellers
    olist_sellers = pd.DataFrame([
        {"seller_id": "sell_01", "seller_zip_code_prefix": 10001, "seller_city": "Sao Paulo", "seller_state": "SP"},
        {"seller_id": "sell_02", "seller_zip_code_prefix": 20002, "seller_city": "Rio De Janeiro", "seller_state": "RJ"},
        {"seller_id": "sell_03", "seller_zip_code_prefix": 80003, "seller_city": "Curitiba", "seller_state": "PR"},
        {"seller_id": "sell_04", "seller_zip_code_prefix": 30004, "seller_city": "Belo Horizonte", "seller_state": "MG"},
    ])

    # 4. 45 Orders across May-August 2018
    n_orders = 45
    order_records = []
    item_records = []
    payment_records = []
    review_records = []

    statuses = ["delivered", "delivered", "delivered", "delivered", "shipped", "canceled", "processing"]
    status_weights = [0.75, 0.05, 0.05, 0.05, 0.04, 0.04, 0.02]

    base_date = datetime(2018, 5, 1, 10, 0)
    for i in range(1, n_orders + 1):
        oid = f"ord_{i:03d}"
        cid = f"cust_{int(rng.integers(1, n_cust + 1)):03d}"
        status = rng.choice(statuses, p=status_weights)

        days_offset = int(rng.integers(0, 110))
        t_purch = base_date + timedelta(days=days_offset, minutes=int(rng.integers(0, 1440)))
        t_app = t_purch + timedelta(minutes=int(rng.integers(5, 60)))
        t_est = t_purch + timedelta(days=int(rng.integers(7, 18)))

        # Fulfillment dates
        if status == "delivered":
            # 85% on-time, 15% delayed
            disp_days = int(rng.integers(1, 4))
            t_disp = t_purch + timedelta(days=disp_days, hours=int(rng.integers(1, 12)))
            deliv_days = disp_days + int(rng.integers(3, 10))
            if rng.random() < 0.15:
                deliv_days += 8  # Delayed beyond estimate
            t_deliv = t_purch + timedelta(days=deliv_days, hours=int(rng.integers(1, 12)))
        elif status == "shipped":
            t_disp = t_purch + timedelta(days=int(rng.integers(1, 3)))
            t_deliv = None
        else:
            t_disp = None
            t_deliv = None

        order_records.append({
            "order_id": oid,
            "customer_id": cid,
            "order_status": status,
            "order_purchase_timestamp": t_purch,
            "order_approved_at": t_app,
            "order_delivered_carrier_date": t_disp,
            "order_delivered_customer_date": t_deliv,
            "order_estimated_delivery_date": t_est,
        })

        # Items: 1 to 2 items per order
        n_items = int(rng.choice([1, 2], p=[0.75, 0.25]))
        order_total = 0.0
        for item_idx in range(1, n_items + 1):
            chosen_spec = product_specs[int(rng.integers(0, len(product_specs)))]
            pid = str(chosen_spec[0])
            price = float(chosen_spec[10])
            freight = float(round(rng.uniform(10.0, 25.0), 2))
            seller = f"sell_{int(rng.integers(1, 5)):02d}"
            order_total += price + freight

            item_records.append({
                "order_id": oid,
                "order_item_id": item_idx,
                "product_id": pid,
                "seller_id": seller,
                "shipping_limit_date": t_purch + timedelta(days=5),
                "price": price,
                "freight_value": freight,
            })

        # Payment
        p_type = rng.choice(["credit_card", "boleto", "voucher", "debit_card"], p=[0.70, 0.18, 0.08, 0.04])
        payment_records.append({
            "order_id": oid,
            "payment_sequential": 1,
            "payment_type": p_type,
            "payment_installments": int(rng.integers(1, 8)) if p_type == "credit_card" else 1,
            "payment_value": round(order_total, 2),
        })

        # Review (for 85% of orders)
        if rng.random() > 0.15:
            score = int(rng.choice([1, 2, 3, 4, 5], p=[0.08, 0.07, 0.15, 0.35, 0.35]))
            comments = {
                5: ("Great product", "Fast shipping and perfect fit."),
                4: ("Good", "Satisfied with the fabric quality."),
                3: ("Average", "Size runs slightly large."),
                2: ("Poor fit", "Fabric feels cheap and size was wrong."),
                1: ("Disappointed", "Delivered late and damaged package."),
            }
            title, msg = comments[score]
            review_records.append({
                "review_id": f"rev_{i:03d}",
                "order_id": oid,
                "review_score": score,
                "review_comment_title": title,
                "review_comment_message": msg,
                "review_creation_date": (t_deliv or t_purch) + timedelta(days=1),
                "review_answer_timestamp": (t_deliv or t_purch) + timedelta(days=2),
            })

    raw_olist = {
        "olist_orders_dataset": pd.DataFrame(order_records),
        "olist_customers_dataset": olist_customers,
        "olist_order_items_dataset": pd.DataFrame(item_records),
        "olist_sellers_dataset": olist_sellers,
        "olist_order_payments_dataset": pd.DataFrame(payment_records),
        "olist_order_reviews_dataset": pd.DataFrame(review_records),
    }
    raw_fashion = {"styles": styles}
    return raw_olist, raw_fashion
