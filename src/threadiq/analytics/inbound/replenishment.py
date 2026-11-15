"""Inbound product recommendations and replenishment decision engine for ThreadIQ."""

from typing import Any, Optional

import numpy as np
import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class ReplenishmentAnalytics(BaseAnalytics):
    """Generates actionable inventory replenishment orders and catalog enrichment priorities."""

    @staticmethod
    def classify_urgency(days_of_cover: Optional[float]) -> str:
        """Classify inventory urgency based on Days of Cover (DoC) thresholds.

        Transparent business rules:
        - <= 7.0 days: CRITICAL (Imminent stockout risk within 1 week)
        - 7.1 to 14.0 days: HIGH (Purchase order required within current cycle)
        - 14.1 to 30.0 days: MEDIUM (Buffer within reorder horizon)
        - > 30.0 days: NORMAL (Adequate inventory buffer)
        - None / NaN: UNAVAILABLE (Insufficient stock or velocity data)
        """
        if days_of_cover is None or pd.isna(days_of_cover):
            return "UNAVAILABLE"
        if days_of_cover <= 7.0:
            return "CRITICAL (Stockout < 7d)"
        elif days_of_cover <= 14.0:
            return "HIGH (Reorder < 14d)"
        elif days_of_cover <= 30.0:
            return "MEDIUM (Monitor < 30d)"
        return "NORMAL"

    def get_replenishment_recommendations(self, max_doc_threshold: float = 30.0) -> pd.DataFrame:
        """Identify SKUs needing urgent replenishment due to low Days of Cover.

        Args:
            max_doc_threshold: Days of Cover upper bound to include in replenishment list (default 30.0 days).

        Returns:
            DataFrame containing current stock, velocity, calculated days of cover, urgency levels, and reorder units.
        """
        sql = """
        SELECT
            p.product_id,
            p.product_display_name,
            p.master_category,
            p.sub_category,
            p.price_reference,
            s.available_quantity as current_stock,
            s.historical_daily_velocity as daily_sales_velocity,
            s.days_of_cover as snapshot_doc,
            s.replenishment_recommendation
        FROM fct_inventory_snapshots s
        JOIN dim_products p ON s.product_id = p.product_id
        WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM fct_inventory_snapshots)
          AND s.days_of_cover <= :threshold
        ORDER BY s.days_of_cover ASC
        """
        df = self.query(sql, {"threshold": max_doc_threshold})

        expected_columns = [
            "product_id",
            "product_display_name",
            "master_category",
            "sub_category",
            "price_reference",
            "current_stock",
            "current_available_stock",
            "daily_sales_velocity",
            "days_of_cover",
            "current_days_of_cover",
            "urgency_level",
            "suggested_reorder_units",
            "replenishment_recommendation",
        ]

        if df.empty:
            return pd.DataFrame(columns=expected_columns)

        # Standardize current stock
        df["current_available_stock"] = df["current_stock"]

        # Calculate days of cover safely
        def _calc_doc(row):
            stock = row.get("current_stock")
            vel = row.get("daily_sales_velocity")
            snap_doc = row.get("snapshot_doc")
            if pd.notnull(stock) and pd.notnull(vel) and vel > 0:
                return round(float(stock) / float(vel), 1)
            elif pd.notnull(snap_doc):
                return round(float(snap_doc), 1)
            return None

        df["days_of_cover"] = df.apply(_calc_doc, axis=1)
        df["current_days_of_cover"] = df["days_of_cover"]

        # Derive urgency level using transparent rules
        df["urgency_level"] = df["days_of_cover"].apply(self.classify_urgency)

        # Suggest 30 days of reorder buffer: max(0, ceil(velocity * 30 - stock))
        def _calc_reorder(row):
            vel = row.get("daily_sales_velocity")
            stock = row.get("current_stock")
            if pd.notnull(vel) and vel > 0 and pd.notnull(stock):
                needed = int(np.ceil(vel * 30.0 - stock))
                return max(0, needed)
            return 0

        df["suggested_reorder_units"] = df.apply(_calc_reorder, axis=1)

        return df

    def get_catalog_enrichment_priorities(self, min_completeness: int = 80) -> pd.DataFrame:
        """Identify revenue-generating or high-traffic products with subpar catalog completeness."""
        sql = """
        SELECT
            p.product_id,
            p.product_display_name,
            p.master_category,
            p.sub_category,
            p.catalog_completeness_score,
            p.price_reference,
            COALESCE(sales.units_sold, 0) as units_sold
        FROM dim_products p
        LEFT JOIN (
            SELECT product_id, COUNT(*) as units_sold
            FROM fct_order_items
            GROUP BY product_id
        ) sales ON p.product_id = sales.product_id
        WHERE p.catalog_completeness_score < :min_completeness
        ORDER BY sales.units_sold DESC, p.catalog_completeness_score ASC
        """
        df = self.query(sql, {"min_completeness": min_completeness})
        if df.empty:
            return pd.DataFrame(columns=[
                "product_id", "product_display_name", "master_category", "sub_category",
                "catalog_completeness_score", "price_reference", "units_sold"
            ])
        return df

    def get_slow_moving_markdown_candidates(self, min_doc: float = 45.0) -> pd.DataFrame:
        """Identify overstocked, slow-moving inventory candidates for promotional markdowns."""
        sql = """
        SELECT
            p.product_id,
            p.product_display_name,
            p.master_category,
            p.sub_category,
            p.price_reference,
            s.available_quantity as current_stock,
            s.historical_daily_velocity as daily_sales_velocity,
            s.days_of_cover
        FROM fct_inventory_snapshots s
        JOIN dim_products p ON s.product_id = p.product_id
        WHERE s.snapshot_date = (SELECT MAX(snapshot_date) FROM fct_inventory_snapshots)
          AND s.days_of_cover >= :min_doc
        ORDER BY s.days_of_cover DESC
        """
        df = self.query(sql, {"min_doc": min_doc})
        if df.empty:
            return pd.DataFrame(columns=[
                "product_id", "product_display_name", "master_category", "sub_category",
                "price_reference", "current_stock", "daily_sales_velocity", "days_of_cover",
                "recommended_discount"
            ])

        df["recommended_discount"] = "25% Markdown Clearance"
        return df
