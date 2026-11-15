"""Outbound order fulfillment lifecycle analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class FulfillmentAnalytics(BaseAnalytics):
    """Analyzes the order fulfillment pipeline from placement to customer delivery."""

    def get_order_status_distribution(self) -> pd.DataFrame:
        """Calculate the distribution and percentage share of orders across lifecycle statuses.

        Returns:
            DataFrame with columns [order_status, order_count, percentage].
            Handles empty tables safely by returning an empty DataFrame with the required schema.
        """
        sql_status = """
        SELECT
            order_status,
            COUNT(*) as order_count,
            ROUND(COUNT(*) * 100.0 / (SELECT NULLIF(COUNT(*), 0) FROM fct_orders), 1) as percentage
        FROM fct_orders
        GROUP BY order_status
        ORDER BY order_count DESC
        """
        df = self.query(sql_status)
        if df.empty:
            return pd.DataFrame(columns=["order_status", "order_count", "percentage"])
        return df

    def get_order_fulfillment_funnel(self) -> dict[str, Any]:
        """Deconstruct the order volume across processing stages."""
        sql = """
        SELECT
            COUNT(*) as total_placed,
            COUNT(approved_at) as total_approved,
            COUNT(s.dispatched_at) as total_dispatched,
            COUNT(s.delivered_customer_date) as total_delivered,
            SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) as total_canceled
        FROM fct_orders o
        LEFT JOIN fct_shipments_deliveries s ON o.order_id = s.order_id
        """
        df = self.query(sql)
        placed = int(df.iloc[0]["total_placed"]) if not df.empty and pd.notnull(df.iloc[0]["total_placed"]) else 0
        approved = int(df.iloc[0]["total_approved"]) if not df.empty and pd.notnull(df.iloc[0]["total_approved"]) else 0
        dispatched = int(df.iloc[0]["total_dispatched"]) if not df.empty and pd.notnull(df.iloc[0]["total_dispatched"]) else 0
        delivered = int(df.iloc[0]["total_delivered"]) if not df.empty and pd.notnull(df.iloc[0]["total_delivered"]) else 0
        canceled = int(df.iloc[0]["total_canceled"]) if not df.empty and pd.notnull(df.iloc[0]["total_canceled"]) else 0

        # Reuse single source of truth for status distribution
        status_df = self.get_order_status_distribution()

        return {
            "orders_placed": MetricResult("Orders Placed", placed, f"{placed:,}", unit="orders", provenance="observed"),
            "orders_approved": MetricResult("Orders Approved", approved, f"{approved:,}", unit="orders", provenance="observed"),
            "orders_dispatched": MetricResult("Orders Dispatched", dispatched, f"{dispatched:,}", unit="orders", provenance="observed"),
            "orders_delivered": MetricResult("Orders Delivered", delivered, f"{delivered:,}", unit="orders", provenance="observed"),
            "orders_canceled": MetricResult("Orders Canceled", canceled, f"{canceled:,}", unit="orders", provenance="observed"),
            "status_distribution": status_df,
        }
