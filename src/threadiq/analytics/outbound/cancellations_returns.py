"""Order cancellation and customer return diagnostics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class CancellationReturnAnalytics(BaseAnalytics):
    """Analyzes cancellation rates, fashion return root-causes, and payment refund exposures."""

    def get_cancellation_and_return_rates(self) -> dict[str, MetricResult]:
        """Compute observed cancellation rate and synthetic return-proxy assignment rate."""
        # 1. Cancellation rate
        sql_cancels = """
        SELECT
            COUNT(*) as total_orders,
            SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) as canceled_orders
        FROM fct_orders
        """
        df_canc = self.query(sql_cancels)
        tot_ord = int(df_canc.iloc[0]["total_orders"]) if not df_canc.empty else 0
        canc_ord = int(df_canc.iloc[0]["canceled_orders"]) if not df_canc.empty else 0
        cancel_rate = self.calc_rate(canc_ord, tot_ord)

        # 2. Return rate (items with a return reason code)
        sql_returns = """
        SELECT
            COUNT(*) as total_items,
            SUM(CASE WHEN return_reason_code IS NOT NULL THEN 1 ELSE 0 END) as returned_items
        FROM fct_order_items
        """
        df_ret = self.query(sql_returns)
        tot_items = int(df_ret.iloc[0]["total_items"]) if not df_ret.empty else 0
        ret_items = int(df_ret.iloc[0]["returned_items"]) if not df_ret.empty else 0
        return_rate = self.calc_rate(ret_items, tot_items)

        return {
            "order_cancellation_rate": MetricResult(
                name="Order Cancellation Rate",
                value=cancel_rate,
                formatted_value=f"{cancel_rate:.1f}%",
                numerator=canc_ord,
                denominator=tot_ord,
                unit="%",
                provenance="observed",
                notes="Percentage of placed orders that were canceled prior to fulfillment.",
            ),
            "item_return_rate": MetricResult(
                name="Synthetic Return-Proxy Assignment Rate",
                value=return_rate,
                formatted_value=f"{return_rate:.1f}%",
                numerator=ret_items,
                denominator=tot_items,
                unit="%",
                provenance="synthetic_proxy",
                notes="Share of order items assigned a synthetic reason proxy from low-review flags only; cancellations are excluded and this is not an observed physical return rate.",
            ),
        }

    def get_return_reasons_breakdown(self) -> pd.DataFrame:
        """Break down synthetic return-reason proxy assignments by fashion category."""
        sql = """
        SELECT
            return_reason_code as return_reason,
            COUNT(*) as return_count,
            ROUND(SUM(price), 2) as refund_value_exposure
        FROM fct_order_items
        WHERE return_reason_code IS NOT NULL
        GROUP BY return_reason_code
        ORDER BY return_count DESC
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame(columns=["return_reason", "return_count", "refund_value_exposure", "share_percentage"])

        tot_returns = df["return_count"].sum()
        df["share_percentage"] = df["return_count"].apply(
            lambda cnt: self.calc_rate(cnt, tot_returns)
        )
        return df

    def get_category_return_patterns(self) -> pd.DataFrame:
        """Analyze synthetic return-proxy assignment rates across garment categories."""
        sql = """
        SELECT
            p.sub_category,
            COUNT(i.order_item_uid) as total_units_sold,
            SUM(CASE WHEN i.return_reason_code IS NOT NULL THEN 1 ELSE 0 END) as returned_units,
            ROUND(SUM(CASE WHEN i.return_reason_code IS NOT NULL THEN i.price ELSE 0 END), 2) as return_value_exposure
        FROM fct_order_items i
        JOIN dim_products p ON i.product_id = p.product_id
        GROUP BY p.sub_category
        ORDER BY total_units_sold DESC
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame()

        df["return_rate"] = df.apply(
            lambda r: self.calc_rate(r["returned_units"], r["total_units_sold"]), axis=1
        )
        return df.sort_values(by="return_rate", ascending=False)
