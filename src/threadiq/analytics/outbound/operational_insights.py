"""Operational bottleneck diagnosis and seller dispatch compliance analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class OperationalInsightsAnalytics(BaseAnalytics):
    """Diagnoses fulfillment bottlenecks, seller SLA breaches, and carrier delay attribution."""

    def get_fulfillment_bottleneck_waterfall(self) -> dict[str, Any]:
        """Decompose average order latency into Order-to-Dispatch vs Dispatch-to-Delivery."""
        sql = """
        SELECT
            ROUND(AVG(order_to_dispatch_hours), 1) as avg_order_to_dispatch_hours,
            ROUND(AVG(dispatch_to_delivery_hours), 1) as avg_dispatch_to_delivery_hours,
            ROUND(AVG(order_to_dispatch_hours + dispatch_to_delivery_hours), 1) as avg_total_hours
        FROM fct_shipments_deliveries
        WHERE delivered_customer_date IS NOT NULL
        """
        df = self.query(sql)
        o2d = float(df.iloc[0]["avg_order_to_dispatch_hours"]) if not df.empty and pd.notnull(df.iloc[0]["avg_order_to_dispatch_hours"]) else 0.0
        d2d = float(df.iloc[0]["avg_dispatch_to_delivery_hours"]) if not df.empty and pd.notnull(df.iloc[0]["avg_dispatch_to_delivery_hours"]) else 0.0
        tot = float(df.iloc[0]["avg_total_hours"]) if not df.empty and pd.notnull(df.iloc[0]["avg_total_hours"]) else 0.0

        o2d_pct = self.calc_rate(o2d, tot)
        d2d_pct = self.calc_rate(d2d, tot)

        primary_bottleneck = "Last-Mile / Transit (Carrier)" if d2d > o2d else "Warehouse / Fulfillment (Seller)"

        return {
            "avg_order_to_dispatch_hours": MetricResult(
                name="Average Order-to-Dispatch Duration",
                value=o2d,
                formatted_value=f"{o2d:.1f} hours ({round(o2d/24.0, 1)} days)",
                unit="hours",
                provenance="observed",
                notes="Duration from customer order approval to carrier pickup.",
            ),
            "avg_dispatch_to_delivery_hours": MetricResult(
                name="Average Dispatch-to-Delivery Duration",
                value=d2d,
                formatted_value=f"{d2d:.1f} hours ({round(d2d/24.0, 1)} days)",
                unit="hours",
                provenance="observed",
                notes="Duration in transit with logistics carrier.",
            ),
            "order_to_dispatch_share_pct": o2d_pct,
            "dispatch_to_delivery_share_pct": d2d_pct,
            "primary_bottleneck": primary_bottleneck,
        }

    def get_seller_dispatch_performance(self) -> pd.DataFrame:
        """Benchmark merchant sellers on fulfillment speed, order volume, and cancellation rates."""
        sql = """
        SELECT
            s.seller_id,
            s.city,
            s.state,
            COUNT(i.order_item_uid) as total_items_fulfilled,
            ROUND(AVG(sh.order_to_dispatch_hours), 1) as avg_dispatch_hours,
            SUM(CASE WHEN sh.order_to_dispatch_hours > 72 THEN 1 ELSE 0 END) as slow_dispatch_count,
            SUM(CASE WHEN sh.is_canceled = 1 THEN 1 ELSE 0 END) as canceled_count
        FROM dim_sellers s
        JOIN fct_order_items i ON s.seller_id = i.seller_id
        LEFT JOIN fct_shipments_deliveries sh ON i.order_id = sh.order_id
        GROUP BY s.seller_id, s.city, s.state
        ORDER BY total_items_fulfilled DESC
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame()

        df["slow_dispatch_rate"] = df.apply(
            lambda r: self.calc_rate(r["slow_dispatch_count"], r["total_items_fulfilled"]), axis=1
        )
        return df
