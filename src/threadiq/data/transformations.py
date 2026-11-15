"""Data transformations and synthetic simulation engine for ThreadIQ.

Constructs canonical star-schema dimension and fact tables, reconciling
observed public data and generating strictly provenanced synthetic telemetry.
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from src.threadiq.config import RANDOM_SEED
from src.threadiq.utils.logging_config import logger


def build_dim_customers(cleaned_customers: pd.DataFrame, orders_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build dim_customers table with cohort month."""
    df = cleaned_customers.copy()

    # Determine customer cohort (month of first purchase)
    if orders_df is not None and not orders_df.empty and "customer_id" in orders_df.columns:
        cust_orders = orders_df.dropna(subset=["purchase_timestamp" if "purchase_timestamp" in orders_df.columns else "order_purchase_timestamp"]).copy()
        ts_col = "purchase_timestamp" if "purchase_timestamp" in cust_orders.columns else "order_purchase_timestamp"
        cust_orders["cohort"] = pd.to_datetime(cust_orders[ts_col]).dt.to_period("M").astype(str)
        first_cohorts = cust_orders.groupby("customer_id")["cohort"].min().to_dict()
        df["customer_cohort"] = df["customer_id"].map(first_cohorts).fillna("2018-01")
    else:
        df["customer_cohort"] = "2018-01"

    dim = pd.DataFrame({
        "customer_id": df["customer_id"],
        "customer_unique_id": df["customer_unique_id"],
        "zip_code_prefix": df["customer_zip_code_prefix"],
        "city": df["customer_city"],
        "state": df["customer_state"],
        "customer_cohort": df["customer_cohort"],
        "data_source": "olist",
    })
    return dim.drop_duplicates(subset=["customer_id"])


def build_dim_sellers(cleaned_sellers: pd.DataFrame) -> pd.DataFrame:
    """Build dim_sellers table."""
    df = cleaned_sellers.copy()
    dim = pd.DataFrame({
        "seller_id": df["seller_id"].astype(str).str.strip(),
        "zip_code_prefix": df["seller_zip_code_prefix"].fillna(0).astype(int).astype(str).str.zfill(5),
        "city": df["seller_city"].fillna("Unknown").astype(str).str.strip().str.title(),
        "state": df["seller_state"].fillna("XX").astype(str).str.strip().str.upper(),
        "data_source": "olist",
    })
    return dim.drop_duplicates(subset=["seller_id"])


def build_dim_products(
    styles_df: pd.DataFrame | None = None,
    olist_products_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build dim_products table with catalog completeness score."""
    records = []

    if styles_df is not None and not styles_df.empty:
        required_attrs = ["gender", "masterCategory", "subCategory", "articleType", "baseColour", "season", "usage"]
        for _, row in styles_df.iterrows():
            populated_count = sum(1 for attr in required_attrs if pd.notnull(row.get(attr)) and str(row.get(attr)).lower() not in ["unknown", "none", "nan", ""])
            completeness_score = int(round((populated_count / len(required_attrs)) * 100))

            records.append({
                "product_id": str(row["id"]),
                "fashion_style_id": str(row["id"]),
                "master_category": str(row.get("masterCategory", "Apparel")),
                "sub_category": str(row.get("subCategory", "Topwear")),
                "article_type": str(row.get("articleType", "T-Shirts")),
                "base_colour": str(row.get("baseColour", "Black")),
                "season": str(row.get("season", "All")),
                "release_year": int(row.get("year", 2018)) if pd.notnull(row.get("year")) else 2018,
                "usage": str(row.get("usage", "Casual")),
                "product_display_name": str(row.get("productDisplayName", "Fashion Product")),
                "price_reference": 59.90,
                "catalog_completeness_score": completeness_score,
                "data_source": "fashion_kaggle",
            })

    elif olist_products_df is not None and not olist_products_df.empty:
        for _, row in olist_products_df.iterrows():
            cat = str(row.get("product_category_name", "apparel"))
            records.append({
                "product_id": str(row["product_id"]),
                "fashion_style_id": None,
                "master_category": "Apparel",
                "sub_category": cat,
                "article_type": cat,
                "base_colour": "Multi",
                "season": "All",
                "release_year": 2018,
                "usage": "Casual",
                "product_display_name": f"Product {cat}",
                "price_reference": 49.99,
                "catalog_completeness_score": 85,
                "data_source": "olist",
            })

    dim = pd.DataFrame(records)
    if dim.empty:
        # Fallback empty schema
        dim = pd.DataFrame(columns=[
            "product_id", "fashion_style_id", "master_category", "sub_category",
            "article_type", "base_colour", "season", "release_year", "usage",
            "product_display_name", "price_reference", "catalog_completeness_score", "data_source"
        ])
    return dim.drop_duplicates(subset=["product_id"])


def build_fct_orders(cleaned_orders: pd.DataFrame) -> pd.DataFrame:
    """Build fct_orders table."""
    df = cleaned_orders.copy()
    fct = pd.DataFrame({
        "order_id": df["order_id"].astype(str),
        "customer_id": df["customer_id"].astype(str),
        "order_status": df["order_status"].astype(str),
        "purchase_timestamp": pd.to_datetime(df["order_purchase_timestamp"]),
        "approved_at": pd.to_datetime(df["order_approved_at"]),
        "estimated_delivery_date": pd.to_datetime(df["order_estimated_delivery_date"]),
        "data_source": "olist",
    })
    return fct.drop_duplicates(subset=["order_id"])


def build_fct_order_items(
    cleaned_items: pd.DataFrame,
    orders_df: pd.DataFrame | None = None,
    reviews_df: pd.DataFrame | None = None,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Build order items with explicitly synthetic reason proxies for low-rated orders only."""
    rng = np.random.default_rng(seed)
    df = cleaned_items.copy()

    # Identify low review orders (score <= 2)
    low_review_orders = set()
    if reviews_df is not None and not reviews_df.empty:
        low_review_orders = set(reviews_df[reviews_df["review_score"] <= 2]["order_id"].unique())

    return_reasons = ["SIZE_FIT", "QUALITY_FABRIC", "STYLE_NOT_AS_PICTURED", "LOGISTICS_DELAY"]
    return_weights = [0.50, 0.25, 0.15, 0.10]

    assigned_reasons = []
    for _, row in df.iterrows():
        oid = row["order_id"]
        # A cancellation is not a return. Low-review flags are only a weak proxy,
        # so generated reason codes are kept explicitly synthetic.
        if oid in low_review_orders:
            reason = rng.choice(return_reasons, p=return_weights)
        else:
            reason = None
        assigned_reasons.append(reason)

    df["order_item_uid"] = df["order_id"].astype(str) + "_" + df["order_item_id"].astype(str)
    fct = pd.DataFrame({
        "order_item_uid": df["order_item_uid"],
        "order_id": df["order_id"].astype(str),
        "order_item_id": df["order_item_id"].astype(int),
        "product_id": df["product_id"].astype(str),
        "seller_id": df["seller_id"].astype(str),
        "shipping_limit_date": pd.to_datetime(df["shipping_limit_date"]) if "shipping_limit_date" in df.columns else None,
        "price": df["price"].astype(float),
        "freight_value": df["freight_value"].astype(float),
        "return_reason_code": assigned_reasons,
        # The order-item transaction is sourced from Olist, but these reason labels
        # are generated proxies inferred from cancellation / low-review flags.
        "return_reason_source": ["synthetic_proxy" if reason is not None else None for reason in assigned_reasons],
        "data_source": "olist",
    })
    return fct.drop_duplicates(subset=["order_item_uid"])


def build_fct_order_payments(payments_df: pd.DataFrame) -> pd.DataFrame:
    """Build fct_order_payments table."""
    df = payments_df.copy()
    df["payment_uid"] = df["order_id"].astype(str) + "_" + df["payment_sequential"].astype(str)
    fct = pd.DataFrame({
        "payment_uid": df["payment_uid"],
        "order_id": df["order_id"].astype(str),
        "payment_sequential": df["payment_sequential"].astype(int),
        "payment_type": df["payment_type"].astype(str),
        "payment_installments": df["payment_installments"].astype(int),
        "payment_value": df["payment_value"].astype(float),
        "data_source": "olist",
    })
    return fct.drop_duplicates(subset=["payment_uid"])


def build_fct_order_reviews(reviews_df: pd.DataFrame) -> pd.DataFrame:
    """Build fct_order_reviews table."""
    df = reviews_df.copy()
    fct = pd.DataFrame({
        "review_id": df["review_id"].astype(str),
        "order_id": df["order_id"].astype(str),
        "review_score": df["review_score"].astype(int),
        "review_comment_title": df["review_comment_title"].astype(str),
        "review_comment_message": df["review_comment_message"].astype(str),
        "review_creation_date": pd.to_datetime(df["review_creation_date"]) if "review_creation_date" in df.columns else None,
        "review_answer_timestamp": pd.to_datetime(df["review_answer_timestamp"]) if "review_answer_timestamp" in df.columns else None,
        "data_source": "olist",
    })
    return fct.drop_duplicates(subset=["review_id"])


def build_fct_shipments_deliveries(
    cleaned_orders: pd.DataFrame,
    cleaned_items: pd.DataFrame,
) -> pd.DataFrame:
    """Build fct_shipments_deliveries table deconstructing fulfillment durations."""
    # Group items to find first seller per order
    seller_map = cleaned_items.groupby("order_id")["seller_id"].first().to_dict()

    df = cleaned_orders.copy()
    t_purch = pd.to_datetime(df["order_purchase_timestamp"])
    t_disp = pd.to_datetime(df["order_delivered_carrier_date"])
    t_deliv = pd.to_datetime(df["order_delivered_customer_date"])
    t_est = pd.to_datetime(df["order_estimated_delivery_date"])

    order_to_dispatch = (t_disp - t_purch).dt.total_seconds() / 3600.0
    dispatch_to_delivery = (t_deliv - t_disp).dt.total_seconds() / 3600.0
    delay_hours = (t_deliv - t_est).dt.total_seconds() / 3600.0

    is_late = (t_deliv > t_est).astype(int)
    is_canceled = (df["order_status"] == "canceled").astype(int)

    fct = pd.DataFrame({
        "shipment_id": df["order_id"].astype(str) + "_shipment",
        "order_id": df["order_id"].astype(str),
        "seller_id": df["order_id"].map(seller_map).fillna("unknown_seller"),
        "dispatched_at": t_disp,
        "delivered_customer_date": t_deliv,
        "estimated_delivery_date": t_est,
        "order_to_dispatch_hours": order_to_dispatch.fillna(0).round().astype(int),
        "dispatch_to_delivery_hours": dispatch_to_delivery.fillna(0).round().astype(int),
        "delivery_delay_hours": delay_hours.fillna(0).round().astype(int),
        "is_late": is_late,
        "is_canceled": is_canceled,
        "carrier_code": "CORREIOS_BR",
        "delivery_region": "BRAZIL_NATIONAL",
        "data_source": "olist",
    })
    return fct.drop_duplicates(subset=["shipment_id"])


def generate_synthetic_sessions_and_events(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    items_df: pd.DataFrame,
    products_df: pd.DataFrame | None = None,
    n_dropoff_sessions: int = 1000,
    seed: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic customer sessions and clickstream event funnel with deterministic seeding.

    Ensures foreign keys in events resolve against valid product_ids in dim_products.
    """
    rng = np.random.default_rng(seed)
    sessions = []
    events = []

    # Compile valid product IDs for referential integrity
    valid_pids: list[str] = []
    if products_df is not None and not products_df.empty:
        valid_pids = products_df["product_id"].astype(str).tolist()
    elif not items_df.empty:
        valid_pids = items_df["product_id"].astype(str).unique().tolist()

    default_pid = valid_pids[0] if valid_pids else None

    order_items_map = items_df.groupby("order_id")["product_id"].apply(list).to_dict()

    # 1. Generate converting sessions from actual orders
    for idx, order in orders_df.head(min(len(orders_df), 1000)).iterrows():
        oid = str(order["order_id"])
        cid = str(order["customer_id"])
        t_purch = pd.to_datetime(order["purchase_timestamp"]) if pd.notnull(order["purchase_timestamp"]) else datetime.now()
        sid = f"sess_{oid}"

        pids = order_items_map.get(oid, [])
        target_pid = str(pids[0]) if pids else default_pid

        device = rng.choice(["mobile", "desktop", "tablet"], p=[0.65, 0.30, 0.05])
        traffic = rng.choice(["organic_search", "direct", "paid_social", "affiliate"], p=[0.40, 0.25, 0.25, 0.10])

        t_start = t_purch - timedelta(minutes=int(rng.integers(10, 45)))
        sessions.append({
            "session_id": sid,
            "customer_id": cid,
            "session_start": t_start,
            "session_end": t_purch + timedelta(minutes=2),
            "device_type": device,
            "traffic_source": traffic,
            "converted_flag": 1,
            "data_source": "synthetic",
        })

        # Funnel events
        t_imp = t_start + timedelta(seconds=10)
        t_view = t_start + timedelta(seconds=int(rng.integers(30, 120)))
        t_cart = t_view + timedelta(seconds=int(rng.integers(60, 240)))
        t_check = t_cart + timedelta(seconds=int(rng.integers(60, 180)))

        events.extend([
            {"event_id": f"{sid}_ev1", "session_id": sid, "customer_id": cid, "event_timestamp": t_imp, "event_type": "impression", "product_id": target_pid, "data_source": "synthetic"},
            {"event_id": f"{sid}_ev2", "session_id": sid, "customer_id": cid, "event_timestamp": t_view, "event_type": "product_view", "product_id": target_pid, "data_source": "synthetic"},
            {"event_id": f"{sid}_ev3", "session_id": sid, "customer_id": cid, "event_timestamp": t_cart, "event_type": "add_to_cart", "product_id": target_pid, "data_source": "synthetic"},
            {"event_id": f"{sid}_ev4", "session_id": sid, "customer_id": cid, "event_timestamp": t_check, "event_type": "checkout_start", "product_id": target_pid, "data_source": "synthetic"},
            {"event_id": f"{sid}_ev5", "session_id": sid, "customer_id": cid, "event_timestamp": t_purch, "event_type": "purchase", "product_id": target_pid, "data_source": "synthetic"},
        ])

    # 2. Generate non-converting drop-off sessions
    cust_ids = customers_df["customer_id"].tolist() if not customers_df.empty else ["cust_mock"]
    for i in range(n_dropoff_sessions):
        sid = f"sess_drop_{i}"
        cid = rng.choice(cust_ids)
        target_pid = rng.choice(valid_pids) if valid_pids else default_pid

        device = rng.choice(["mobile", "desktop", "tablet"], p=[0.65, 0.30, 0.05])
        traffic = rng.choice(["organic_search", "direct", "paid_social", "affiliate"], p=[0.40, 0.25, 0.25, 0.10])
        t_start = datetime(2018, 5, 1) + timedelta(minutes=int(rng.integers(0, 120000)))

        sessions.append({
            "session_id": sid,
            "customer_id": cid,
            "session_start": t_start,
            "session_end": t_start + timedelta(minutes=int(rng.integers(2, 15))),
            "device_type": device,
            "traffic_source": traffic,
            "converted_flag": 0,
            "data_source": "synthetic",
        })

        # Realistic drop-off stages referencing valid product ID
        events.append({"event_id": f"{sid}_ev1", "session_id": sid, "customer_id": cid, "event_timestamp": t_start, "event_type": "impression", "product_id": target_pid, "data_source": "synthetic"})
        if rng.random() > 0.40:  # 60% view product
            events.append({"event_id": f"{sid}_ev2", "session_id": sid, "customer_id": cid, "event_timestamp": t_start + timedelta(seconds=30), "event_type": "product_view", "product_id": target_pid, "data_source": "synthetic"})
            if rng.random() > 0.70:  # 30% of viewers add to cart
                events.append({"event_id": f"{sid}_ev3", "session_id": sid, "customer_id": cid, "event_timestamp": t_start + timedelta(seconds=90), "event_type": "add_to_cart", "product_id": target_pid, "data_source": "synthetic"})
                if rng.random() > 0.50:  # 50% start checkout but abandon
                    events.append({"event_id": f"{sid}_ev4", "session_id": sid, "customer_id": cid, "event_timestamp": t_start + timedelta(seconds=150), "event_type": "checkout_start", "product_id": target_pid, "data_source": "synthetic"})

    return pd.DataFrame(sessions), pd.DataFrame(events)


def generate_synthetic_inventory_snapshots(
    products_df: pd.DataFrame,
    days: int = 30,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate daily SKU-level inventory snapshots with stockout and Days of Cover metrics."""
    rng = np.random.default_rng(seed)
    snapshots = []
    base_date = datetime(2018, 8, 1).date()

    pids = products_df["product_id"].head(min(len(products_df), 100)).tolist() if not products_df.empty else ["mock_sku"]

    for pid in pids:
        current_soh = int(rng.integers(5, 80))
        velocity = float(round(rng.uniform(0.5, 4.0), 2))

        for d in range(days):
            snap_date = base_date + timedelta(days=d)
            # Daily sales draw
            units_sold = int(rng.poisson(velocity))
            current_soh = max(0, current_soh - units_sold)

            # Replenish if empty
            if current_soh == 0 and rng.random() > 0.6:
                current_soh = int(rng.integers(20, 60))

            reserved = min(current_soh, int(rng.integers(0, 5)))
            available = current_soh - reserved
            stockout = 1 if available <= 0 else 0
            doc = round(available / max(velocity, 0.1), 1)

            if doc < 7.0:
                rec = "CRITICAL_REPLENISHMENT"
            elif doc > 45.0:
                rec = "EXCESS_STOCK"
            else:
                rec = "HEALTHY"

            snapshots.append({
                "snapshot_id": f"{pid}_{snap_date}",
                "product_id": str(pid),
                "snapshot_date": snap_date,
                "stock_on_hand": current_soh,
                "reserved_stock": reserved,
                "available_stock": available,
                "historical_daily_velocity": velocity,
                "days_of_cover": doc,
                "stockout_flag": stockout,
                "replenishment_recommendation": rec,
                "data_source": "synthetic",
            })

    return pd.DataFrame(snapshots)
