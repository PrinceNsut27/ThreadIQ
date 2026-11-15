"""Inventory availability, stockout modeling, and velocity analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class InventoryAnalytics(BaseAnalytics):
    """Analyzes daily stock availability, stockout frequencies/durations, and SKU velocity tiers."""

    def get_stockout_summary(self) -> dict[str, MetricResult]:
        """Calculate overall stockout rate and in-stock availability rate."""
        sql = """
        SELECT
            COUNT(*) as total_snapshot_days,
            SUM(stockout_flag) as stockout_days,
            AVG(available_quantity) as avg_available_stock,
            AVG(days_of_cover) as avg_days_of_cover
        FROM fct_inventory_snapshots
        """
        df = self.query(sql)
        tot_days = int(df.iloc[0]["total_snapshot_days"]) if not df.empty else 0
        so_days = int(df.iloc[0]["stockout_days"]) if not df.empty else 0
        stockout_rate = self.calc_rate(so_days, tot_days)
        in_stock_rate = round(100.0 - stockout_rate, 2)
        avg_doc = round(float(df.iloc[0]["avg_days_of_cover"]), 1) if not df.empty and pd.notnull(df.iloc[0]["avg_days_of_cover"]) else 0.0

        return {
            "stockout_rate": MetricResult(
                name="Stockout Rate (SKU-Days)",
                value=stockout_rate,
                formatted_value=f"{stockout_rate:.1f}%",
                numerator=so_days,
                denominator=tot_days,
                unit="%",
                provenance="synthetic",
                notes="Proportion of daily SKU snapshots where available stock was zero.",
            ),
            "in_stock_availability_rate": MetricResult(
                name="In-Stock Availability Rate",
                value=in_stock_rate,
                formatted_value=f"{in_stock_rate:.1f}%",
                unit="%",
                provenance="synthetic",
                notes="Proportion of active SKU-days where items were available to purchase.",
            ),
            "average_days_of_cover": MetricResult(
                name="Average Days of Cover",
                value=avg_doc,
                formatted_value=f"{avg_doc:.1f} days",
                unit="days",
                provenance="synthetic",
                notes="Available stock divided by trailing daily sales velocity.",
            ),
        }

    def get_sku_stockout_frequency(self) -> pd.DataFrame:
        """Calculate stockout frequency and longest duration per SKU."""
        sql = """
        SELECT
            p.product_id,
            p.product_display_name,
            p.master_category,
            p.sub_category,
            COUNT(s.snapshot_date) as monitored_days,
            SUM(s.stockout_flag) as stockout_days,
            ROUND(AVG(s.available_quantity), 1) as avg_available_quantity,
            ROUND(AVG(s.historical_daily_velocity), 2) as avg_daily_velocity,
            ROUND(AVG(s.days_of_cover), 1) as avg_days_of_cover
        FROM dim_products p
        JOIN fct_inventory_snapshots s ON p.product_id = s.product_id
        GROUP BY p.product_id, p.product_display_name, p.master_category, p.sub_category
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame()

        df["stockout_frequency_pct"] = df.apply(
            lambda r: self.calc_rate(r["stockout_days"], r["monitored_days"]), axis=1
        )
        return df.sort_values(by="stockout_frequency_pct", ascending=False)

    def get_high_demand_vs_slow_moving_skus(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Categorize SKUs into high-demand fast movers vs slow-moving inventory liabilities.

        Returns:
            tuple of (high_demand_df, slow_moving_df)
        """
        df_skus = self.get_sku_stockout_frequency()
        if df_skus.empty:
            return pd.DataFrame(), pd.DataFrame()

        # High demand: top 25% by velocity or velocity >= 3.0
        high_demand = df_skus[df_skus["avg_daily_velocity"] >= 3.0].sort_values(by="avg_daily_velocity", ascending=False)

        # Slow moving: velocity < 1.0 and Days of Cover > 40
        slow_moving = df_skus[(df_skus["avg_daily_velocity"] < 1.0) & (df_skus["avg_days_of_cover"] > 40.0)].sort_values(by="avg_days_of_cover", ascending=False)

        return high_demand, slow_moving
