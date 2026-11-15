"""Customer behavioral analytics and cohort retention for ThreadIQ."""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class CustomerAnalytics(BaseAnalytics):
    """Calculates customer metrics: AOV, repeat purchase rates, cohorts, and RFM segmentation."""

    def get_repeat_purchase_metrics(self) -> dict[str, MetricResult]:
        """Compute new vs returning customer split and repeat purchase rate."""
        sql = """
        SELECT
            c.customer_unique_id,
            COUNT(DISTINCT o.order_id) as order_count,
            SUM(p.payment_value) as total_spend
        FROM dim_customers c
        JOIN fct_orders o ON c.customer_id = o.customer_id
        JOIN fct_order_payments p ON o.order_id = p.order_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY c.customer_unique_id
        """
        df = self.query(sql)
        total_unique = len(df)
        repeat_customers = int((df["order_count"] > 1).sum()) if total_unique > 0 else 0
        repeat_rate = self.calc_rate(repeat_customers, total_unique)

        return {
            "total_unique_customers": MetricResult(
                name="Total Unique Customers",
                value=total_unique,
                formatted_value=f"{total_unique:,}",
                unit="customers",
                provenance="observed",
                notes="Distinct consumers identified via customer_unique_id.",
            ),
            "repeat_customers_count": MetricResult(
                name="Repeat Customers Count",
                value=repeat_customers,
                formatted_value=f"{repeat_customers:,}",
                unit="customers",
                provenance="observed",
                notes="Customers who completed 2 or more distinct orders.",
            ),
            "repeat_purchase_rate": MetricResult(
                name="Repeat Purchase Rate",
                value=repeat_rate,
                formatted_value=f"{repeat_rate:.1f}%",
                numerator=repeat_customers,
                denominator=total_unique,
                unit="%",
                provenance="observed",
                notes="Percentage of unique consumers with multiple purchases.",
            ),
        }

    def get_average_order_value(self) -> MetricResult:
        """Calculate Average Order Value (AOV) across valid orders."""
        sql = """
        SELECT
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(p.payment_value) as total_gross_value
        FROM fct_orders o
        JOIN fct_order_payments p ON o.order_id = p.order_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
        """
        df = self.query(sql)
        tot_orders = int(df.iloc[0]["total_orders"]) if not df.empty and pd.notnull(df.iloc[0]["total_orders"]) else 0
        tot_rev = float(df.iloc[0]["total_gross_value"]) if not df.empty and pd.notnull(df.iloc[0]["total_gross_value"]) else 0.0
        aov = round(tot_rev / tot_orders, 2) if tot_orders > 0 else 0.0

        return MetricResult(
            name="Average Order Value (AOV)",
            value=aov,
            formatted_value=f"${aov:.2f}",
            numerator=tot_rev,
            denominator=tot_orders,
            unit="$",
            provenance="observed",
            notes="Total revenue divided by valid completed orders.",
        )

    def get_monthly_cohort_retention(self) -> pd.DataFrame:
        """Calculate cohort acquisition and subsequent monthly order retention."""
        sql = """
        SELECT
            c.customer_unique_id,
            c.customer_cohort as cohort_month,
            strftime('%Y-%m', o.purchase_timestamp) as order_month
        FROM dim_customers c
        JOIN fct_orders o ON c.customer_id = o.customer_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame(columns=["cohort_month", "cohort_size", "month_0", "month_1", "retention_rate_m1"])

        # Cohort sizes
        cohort_sizes = df.groupby("cohort_month")["customer_unique_id"].nunique().to_dict()

        # Month difference
        df["cohort_dt"] = pd.to_datetime(df["cohort_month"])
        df["order_dt"] = pd.to_datetime(df["order_month"])
        df["period_number"] = (
            (df["order_dt"].dt.year - df["cohort_dt"].dt.year) * 12 +
            (df["order_dt"].dt.month - df["cohort_dt"].dt.month)
        )

        cohort_retention = df.pivot_table(
            index="cohort_month",
            columns="period_number",
            values="customer_unique_id",
            aggfunc="nunique",
            fill_value=0,
        ).reset_index()

        cohort_retention["cohort_size"] = cohort_retention["cohort_month"].map(cohort_sizes)
        return cohort_retention

    def get_rfm_customer_segments(self) -> pd.DataFrame:
        """Perform Recency, Frequency, Monetary (RFM) behavioral customer segmentation."""
        sql = """
        SELECT
            c.customer_unique_id,
            MAX(o.purchase_timestamp) as last_purchase_date,
            COUNT(DISTINCT o.order_id) as frequency,
            SUM(p.payment_value) as monetary_value
        FROM dim_customers c
        JOIN fct_orders o ON c.customer_id = o.customer_id
        JOIN fct_order_payments p ON o.order_id = p.order_id
        WHERE o.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY c.customer_unique_id
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame()

        df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"])
        reference_date = df["last_purchase_date"].max()
        df["recency_days"] = (reference_date - df["last_purchase_date"]).dt.days

        # Assign segments based on frequency & recency
        def segment_user(row):
            if row["frequency"] >= 2 and row["recency_days"] <= 45:
                return "Champions (Loyal High Value)"
            elif row["frequency"] >= 2 and row["recency_days"] > 45:
                return "At Risk (Past Repeaters)"
            elif row["frequency"] == 1 and row["recency_days"] <= 30:
                return "New Recent Customers"
            else:
                return "Dormant One-Time Buyers"

        df["segment"] = df.apply(segment_user, axis=1)
        return df.sort_values(by="monetary_value", ascending=False)
