"""Logistics SLA and delivery performance analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class DeliveryPerformanceAnalytics(BaseAnalytics):
    """Analyzes transit times, On-Time Delivery (OTD%) rates, and carrier/regional performance."""

    def get_delivery_sla_metrics(self) -> dict[str, MetricResult]:
        """Calculate overall On-Time Delivery Rate (OTD%), late delivery rate, and average transit duration."""
        sql = """
        SELECT
            COUNT(*) as total_delivered,
            SUM(is_late) as total_late,
            AVG(dispatch_to_delivery_hours) as avg_transit_hours,
            AVG(order_to_dispatch_hours) as avg_dispatch_hours,
            AVG(order_to_dispatch_hours + dispatch_to_delivery_hours) as avg_total_delivery_hours
        FROM fct_shipments_deliveries
        WHERE delivered_customer_date IS NOT NULL
        """
        df = self.query(sql)
        tot_deliv = int(df.iloc[0]["total_delivered"]) if not df.empty and pd.notnull(df.iloc[0]["total_delivered"]) else 0
        tot_late = int(df.iloc[0]["total_late"]) if not df.empty and pd.notnull(df.iloc[0]["total_late"]) else 0

        late_rate = self.calc_rate(tot_late, tot_deliv)
        otd_rate = round(100.0 - late_rate, 2)

        avg_hours = float(df.iloc[0]["avg_total_delivery_hours"]) if not df.empty and pd.notnull(df.iloc[0]["avg_total_delivery_hours"]) else 0.0
        avg_days = round(avg_hours / 24.0, 1)

        return {
            "on_time_delivery_rate": MetricResult(
                name="On-Time Delivery Rate (OTD%)",
                value=otd_rate,
                formatted_value=f"{otd_rate:.1f}%",
                numerator=tot_deliv - tot_late,
                denominator=tot_deliv,
                unit="%",
                provenance="observed",
                notes="Delivered shipments where actual arrival was on or before estimated date.",
            ),
            "late_delivery_rate": MetricResult(
                name="Late Delivery Rate",
                value=late_rate,
                formatted_value=f"{late_rate:.1f}%",
                numerator=tot_late,
                denominator=tot_deliv,
                unit="%",
                provenance="observed",
                notes="Shipments delivered after the promised delivery estimate.",
            ),
            "average_delivery_time": MetricResult(
                name="Average Delivery Time",
                value=avg_days,
                formatted_value=f"{avg_days:.1f} days",
                unit="days",
                provenance="observed",
                notes="Mean total duration from purchase to customer delivery.",
            ),
        }

    def get_regional_delivery_performance(self) -> pd.DataFrame:
        """Analyze delivery duration, OTD%, and delay rates segmented by customer state/destination region."""
        sql = """
        SELECT
            c.state as destination_state,
            COUNT(s.shipment_id) as total_shipments,
            SUM(s.is_late) as late_shipments,
            ROUND(AVG(s.dispatch_to_delivery_hours) / 24.0, 1) as avg_transit_days,
            ROUND(AVG(s.delivery_delay_hours) / 24.0, 1) as avg_delay_days
        FROM fct_shipments_deliveries s
        JOIN fct_orders o ON s.order_id = o.order_id
        JOIN dim_customers c ON o.customer_id = c.customer_id
        WHERE s.delivered_customer_date IS NOT NULL
        GROUP BY c.state
        ORDER BY total_shipments DESC
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame()

        df["on_time_rate"] = df.apply(
            lambda r: round(100.0 - self.calc_rate(r["late_shipments"], r["total_shipments"]), 1),
            axis=1,
        )
        df["average_transit_days"] = df["avg_transit_days"]
        return df
