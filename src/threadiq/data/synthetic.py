"""Synthetic fashion commerce behavioural and operational data generator for ThreadIQ.

Generates realistic, chronologically consistent clickstream event journeys,
dynamic daily inventory snapshots with demand archetypes, and marketing promotions.
Strictly tagged with source_type = 'synthetic'.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from src.threadiq.config import RANDOM_SEED
from src.threadiq.utils.logging_config import logger


@dataclass
class SyntheticConfig:
    """Configuration parameters for synthetic data generation."""
    seed: int = RANDOM_SEED
    n_dropoff_sessions: int = 1500
    max_order_sessions: int = 1000
    inventory_days: int = 60
    inventory_start_date: date = date(2018, 6, 1)
    n_promotions: int = 30


class SyntheticDataGenerator:
    """Engine generating fashion e-commerce clickstream journeys, inventory, and promotions."""

    def __init__(self, config: SyntheticConfig | None = None):
        self.config = config or SyntheticConfig()
        self.rng = np.random.default_rng(self.config.seed)

    def generate_clickstream_dataset(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        orders_df: pd.DataFrame | None = None,
        items_df: pd.DataFrame | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate realistic user browsing sessions and multi-step clickstream event funnels.

        Returns:
            tuple of (fct_sessions, fct_events_clickstream, fct_search_queries)
        """
        logger.info(f"Generating synthetic clickstream with seed={self.config.seed}...")
        sessions: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        searches: list[dict[str, Any]] = []

        # Reference sets for referential integrity
        cust_ids = customers_df["customer_id"].astype(str).tolist() if not customers_df.empty else ["cust_sim_01"]
        product_records = products_df.to_dict(orient="records") if not products_df.empty else [{
            "product_id": "prod_sim_01",
            "sub_category": "T-Shirts",
            "price_reference": 49.99,
            "product_display_name": "Cotton Crew Neck T-Shirt",
        }]

        product_id_map = {str(p["product_id"]): p for p in product_records}
        all_product_ids = list(product_id_map.keys())

        # Map order items for converting sessions
        order_items_map: dict[str, list[dict[str, Any]]] = {}
        if items_df is not None and not items_df.empty:
            for oid, grp in items_df.groupby("order_id"):
                order_items_map[str(oid)] = grp.to_dict(orient="records")

        # ----------------------------------------------------
        # 1. GENERATE CONVERTING SESSIONS (Tied to real orders)
        # ----------------------------------------------------
        if orders_df is not None and not orders_df.empty:
            eligible_orders = orders_df.head(self.config.max_order_sessions)
            for _, order in eligible_orders.iterrows():
                oid = str(order["order_id"])
                cid = str(order["customer_id"])
                t_purch = pd.to_datetime(order.get("purchase_timestamp", order.get("order_purchase_timestamp", datetime(2018, 6, 15, 14, 0))))

                items = order_items_map.get(oid, [])
                if items:
                    purchased_pid = str(items[0].get("product_id", all_product_ids[0]))
                    purchased_price = float(items[0].get("price", 49.99))
                else:
                    purchased_pid = self.rng.choice(all_product_ids)
                    purchased_price = float(product_id_map[purchased_pid].get("price_reference", 49.99))

                prod_meta = product_id_map.get(purchased_pid, product_records[0])
                category = prod_meta.get("sub_category", "Apparel")

                sid = f"sess_ord_{oid}"
                device = self.rng.choice(["mobile", "desktop", "tablet"], p=[0.65, 0.30, 0.05])
                traffic = self.rng.choice(["organic_search", "direct", "paid_social", "affiliate"], p=[0.40, 0.25, 0.25, 0.10])

                # Journey duration: 15-40 minutes before purchase
                duration_mins = int(self.rng.integers(15, 40))
                t_start = t_purch - timedelta(minutes=duration_mins)

                sessions.append({
                    "session_id": sid,
                    "customer_id": cid,
                    "session_start": t_start,
                    "session_end": t_purch + timedelta(minutes=2),
                    "device_type": device,
                    "traffic_source": traffic,
                    "converted_flag": 1,
                    "source_type": "synthetic",
                    "data_source": "synthetic",
                })

                # Sequence: Homepage -> Search/Category -> Product Impression -> Product View -> Add to Wishlist (optional) -> Add to Cart -> Checkout Started -> Payment Attempted -> Purchase Completed
                cur_t = t_start
                step = 1

                # Step 1: Homepage
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "homepage_impression",
                    "product_id": None, "category": None, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": None,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

                # Step 2: Category or Search
                cur_t += timedelta(seconds=int(self.rng.integers(20, 60)))
                step += 1
                query_term = str(prod_meta.get("product_display_name", category)).lower()[:30]

                if self.rng.random() > 0.40:
                    events.append({
                        "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                        "event_timestamp": cur_t, "event_type": "search_query",
                        "product_id": None, "category": category, "search_query": query_term,
                        "device_type": device, "traffic_source": traffic, "price_at_event": None,
                        "source_type": "synthetic", "data_source": "synthetic",
                    })
                    searches.append({
                        "query_id": f"qry_{sid}", "session_id": sid, "customer_id": cid,
                        "query_timestamp": cur_t, "search_term": query_term,
                        "result_count": int(self.rng.integers(12, 150)), "zero_result_flag": 0,
                        "clicked_product_id": purchased_pid, "source_type": "synthetic", "data_source": "synthetic",
                    })
                else:
                    events.append({
                        "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                        "event_timestamp": cur_t, "event_type": "category_page_view",
                        "product_id": None, "category": category, "search_query": None,
                        "device_type": device, "traffic_source": traffic, "price_at_event": None,
                        "source_type": "synthetic", "data_source": "synthetic",
                    })

                # Step 3: Product View
                cur_t += timedelta(seconds=int(self.rng.integers(30, 90)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "product_detail_view",
                    "product_id": purchased_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": purchased_price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

                # Step 4: Optional Wishlist
                if self.rng.random() > 0.65:
                    cur_t += timedelta(seconds=int(self.rng.integers(15, 45)))
                    step += 1
                    events.append({
                        "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                        "event_timestamp": cur_t, "event_type": "add_to_wishlist",
                        "product_id": purchased_pid, "category": category, "search_query": None,
                        "device_type": device, "traffic_source": traffic, "price_at_event": purchased_price,
                        "source_type": "synthetic", "data_source": "synthetic",
                    })

                # Step 5: Add to Cart
                cur_t += timedelta(seconds=int(self.rng.integers(30, 80)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "add_to_cart",
                    "product_id": purchased_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": purchased_price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

                # Step 6: Checkout Started
                cur_t += timedelta(seconds=int(self.rng.integers(40, 120)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "checkout_started",
                    "product_id": purchased_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": purchased_price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

                # Step 7: Payment Attempted
                cur_t += timedelta(seconds=int(self.rng.integers(30, 90)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "payment_attempted",
                    "product_id": purchased_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": purchased_price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

                # Step 8: Purchase Completed
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": t_purch, "event_type": "purchase_completed",
                    "product_id": purchased_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": purchased_price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

        # ----------------------------------------------------
        # 2. GENERATE NON-CONVERTING DROP-OFF SESSIONS
        # ----------------------------------------------------
        journey_archetypes = [
            "search_zero_result",   # 10%
            "window_shopper_bounce", # 30%
            "wishlist_drop",        # 20%
            "cart_abandonment",     # 25%
            "cart_removal",         # 15%
        ]
        archetype_weights = [0.10, 0.30, 0.20, 0.25, 0.15]

        base_start = datetime(2018, 5, 1, 8, 0)
        time_span_minutes = 120 * 24 * 60  # 120 days

        for i in range(self.config.n_dropoff_sessions):
            sid = f"sess_drop_{i:04d}"
            cid = self.rng.choice(cust_ids)
            device = self.rng.choice(["mobile", "desktop", "tablet"], p=[0.65, 0.30, 0.05])
            traffic = self.rng.choice(["organic_search", "direct", "paid_social", "affiliate"], p=[0.40, 0.25, 0.25, 0.10])
            archetype = self.rng.choice(journey_archetypes, p=archetype_weights)

            target_pid = self.rng.choice(all_product_ids)
            prod_meta = product_id_map[target_pid]
            category = prod_meta.get("sub_category", "Apparel")
            price = float(prod_meta.get("price_reference", 49.99))

            t_start = base_start + timedelta(minutes=int(self.rng.integers(0, time_span_minutes)))
            cur_t = t_start
            step = 1

            # All start with homepage
            events.append({
                "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                "event_timestamp": cur_t, "event_type": "homepage_impression",
                "product_id": None, "category": None, "search_query": None,
                "device_type": device, "traffic_source": traffic, "price_at_event": None,
                "source_type": "synthetic", "data_source": "synthetic",
            })

            if archetype == "search_zero_result":
                cur_t += timedelta(seconds=int(self.rng.integers(10, 30)))
                step += 1
                rare_query = self.rng.choice(["vintage velvet kimono", "waterproof neon tux", "titanium trenchcoat", "gold sequin sneakers"])
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "search_query",
                    "product_id": None, "category": None, "search_query": rare_query,
                    "device_type": device, "traffic_source": traffic, "price_at_event": None,
                    "source_type": "synthetic", "data_source": "synthetic",
                })
                searches.append({
                    "query_id": f"qry_{sid}", "session_id": sid, "customer_id": cid,
                    "query_timestamp": cur_t, "search_term": rare_query,
                    "result_count": 0, "zero_result_flag": 1,
                    "clicked_product_id": None, "source_type": "synthetic", "data_source": "synthetic",
                })

            elif archetype == "window_shopper_bounce":
                cur_t += timedelta(seconds=int(self.rng.integers(15, 45)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "product_detail_view",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

            elif archetype == "wishlist_drop":
                cur_t += timedelta(seconds=int(self.rng.integers(20, 50)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "product_detail_view",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })
                cur_t += timedelta(seconds=int(self.rng.integers(15, 30)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "add_to_wishlist",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

            elif archetype == "cart_abandonment":
                cur_t += timedelta(seconds=int(self.rng.integers(20, 60)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "product_detail_view",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })
                cur_t += timedelta(seconds=int(self.rng.integers(20, 60)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "add_to_cart",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })
                cur_t += timedelta(seconds=int(self.rng.integers(30, 90)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "checkout_started",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

            elif archetype == "cart_removal":
                cur_t += timedelta(seconds=int(self.rng.integers(20, 50)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "product_detail_view",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })
                cur_t += timedelta(seconds=int(self.rng.integers(20, 60)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "add_to_cart",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })
                cur_t += timedelta(seconds=int(self.rng.integers(15, 45)))
                step += 1
                events.append({
                    "event_id": f"ev_{sid}_{step:02d}", "session_id": sid, "customer_id": cid,
                    "event_timestamp": cur_t, "event_type": "remove_from_cart",
                    "product_id": target_pid, "category": category, "search_query": None,
                    "device_type": device, "traffic_source": traffic, "price_at_event": price,
                    "source_type": "synthetic", "data_source": "synthetic",
                })

            sessions.append({
                "session_id": sid,
                "customer_id": cid,
                "session_start": t_start,
                "session_end": cur_t + timedelta(seconds=15),
                "device_type": device,
                "traffic_source": traffic,
                "converted_flag": 0,
                "source_type": "synthetic",
                "data_source": "synthetic",
            })

        df_sessions = pd.DataFrame(sessions).drop_duplicates(subset=["session_id"])
        df_events = pd.DataFrame(events).drop_duplicates(subset=["event_id"])
        df_searches = pd.DataFrame(searches).drop_duplicates(subset=["query_id"])

        logger.info(f"Generated {len(df_sessions):,} sessions, {len(df_events):,} clickstream events, {len(df_searches):,} search queries.")
        return df_sessions, df_events, df_searches

    def generate_inventory_dataset(
        self,
        products_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate daily inventory snapshots across demand archetypes and simulated warehouses."""
        logger.info(f"Generating synthetic inventory snapshots ({self.config.inventory_days} days)...")
        snapshots: list[dict[str, Any]] = []
        product_records = products_df.to_dict(orient="records") if not products_df.empty else [{
            "product_id": "prod_sim_01", "sub_category": "T-Shirts"
        }]

        warehouses = ["WH_NORTH_01", "WH_SOUTH_02", "WH_CENTRAL_01"]
        demand_archetypes = ["FAST_MOVER", "STEADY_STAPLE", "SLOW_MOVER", "SEASONAL_SURGE"]
        archetype_probs = [0.15, 0.50, 0.25, 0.10]

        for p in product_records:
            pid = str(p["product_id"])
            archetype = self.rng.choice(demand_archetypes, p=archetype_probs)
            wh = self.rng.choice(warehouses)

            # Velocity parameters
            if archetype == "FAST_MOVER":
                base_velocity = float(self.rng.uniform(6.0, 14.0))
                current_stock = int(self.rng.integers(30, 90))
                reorder_threshold = 20
                batch_replenish = 80
            elif archetype == "STEADY_STAPLE":
                base_velocity = float(self.rng.uniform(1.5, 4.0))
                current_stock = int(self.rng.integers(20, 60))
                reorder_threshold = 10
                batch_replenish = 40
            elif archetype == "SLOW_MOVER":
                base_velocity = float(self.rng.uniform(0.1, 0.8))
                current_stock = int(self.rng.integers(15, 40))
                reorder_threshold = 3
                batch_replenish = 15
            else:  # SEASONAL_SURGE
                base_velocity = float(self.rng.uniform(2.0, 5.0))
                current_stock = int(self.rng.integers(40, 100))
                reorder_threshold = 25
                batch_replenish = 90

            for d in range(self.config.inventory_days):
                snap_date = self.config.inventory_start_date + timedelta(days=d)

                # Seasonal surge acceleration in middle 20 days
                daily_vel = base_velocity
                if archetype == "SEASONAL_SURGE" and 20 <= d <= 40:
                    daily_vel *= 2.5

                units_sold = int(self.rng.poisson(daily_vel))
                replenished_qty = 0

                # Replenish event trigger
                if current_stock <= reorder_threshold and self.rng.random() > 0.40:
                    replenished_qty = batch_replenish
                    current_stock += replenished_qty

                # Deplete stock
                current_stock = max(0, current_stock - units_sold)

                # Reserve stock (locked in ongoing checkouts)
                reserved = min(current_stock, int(self.rng.integers(0, 4)))
                available = max(0, current_stock - reserved)

                stockout = 1 if available == 0 else 0
                doc = round(available / max(daily_vel, 0.1), 1)

                if doc < 7.0:
                    rec = "CRITICAL_REPLENISHMENT"
                elif doc > 50.0:
                    rec = "EXCESS_STOCK"
                else:
                    rec = "HEALTHY"

                snapshots.append({
                    "snapshot_id": f"{pid}_{snap_date}",
                    "product_id": pid,
                    "snapshot_date": snap_date,
                    "stock_on_hand": current_stock,
                    "reserved_quantity": reserved,
                    "available_quantity": available,
                    "warehouse_id": wh,
                    "replenishment_quantity": replenished_qty,
                    "historical_daily_velocity": round(daily_vel, 2),
                    "days_of_cover": doc,
                    "stockout_flag": stockout,
                    "replenishment_recommendation": rec,
                    "source_type": "synthetic",
                    "data_source": "synthetic",
                })

        df_inv = pd.DataFrame(snapshots).drop_duplicates(subset=["snapshot_id"])
        logger.info(f"Generated {len(df_inv):,} inventory snapshots across {len(product_records)} SKUs.")
        return df_inv

    def generate_promotions_dataset(
        self,
        products_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate promotional campaigns with valid markdown depths and non-inverting dates."""
        logger.info(f"Generating synthetic promotions...")
        promos: list[dict[str, Any]] = []

        product_records = products_df.to_dict(orient="records") if not products_df.empty else [{
            "product_id": "prod_sim_01", "sub_category": "T-Shirts"
        }]

        promo_types = ["SEASONAL_CLEARANCE", "FLASH_SALE", "CATEGORY_DISCOUNT", "NEW_CUSTOMER_VOUCHER"]
        discounts = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]

        for i in range(self.config.n_promotions):
            pid_choice = str(self.rng.choice(product_records)["product_id"])
            cat_choice = self.rng.choice(["Topwear", "Bottomwear", "Footwear", "Apparel"])
            discount = float(self.rng.choice(discounts))
            p_type = self.rng.choice(promo_types)

            # Valid start and end dates
            start_offset = int(self.rng.integers(0, 45))
            duration_days = int(self.rng.integers(5, 21))
            start_d = self.config.inventory_start_date + timedelta(days=start_offset)
            end_d = start_d + timedelta(days=duration_days)

            promos.append({
                "promotion_id": f"promo_{i+1:03d}",
                "product_id": pid_choice,
                "category": cat_choice,
                "discount_percentage": discount,
                "start_date": start_d,
                "end_date": end_d,
                "promotion_type": p_type,
                "source_type": "synthetic",
                "data_source": "synthetic",
            })

        df_promos = pd.DataFrame(promos).drop_duplicates(subset=["promotion_id"])
        logger.info(f"Generated {len(df_promos):,} promotion records.")
        return df_promos
