"""Storefront conversion funnel analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult
from src.threadiq.utils.logging_config import logger


class FunnelAnalytics(BaseAnalytics):
    """Calculates customer funnel progression, stage conversions, and drop-off leakages."""

    FUNNEL_STAGES = [
        "homepage_impression",
        "product_detail_view",
        "add_to_cart",
        "checkout_started",
        "payment_attempted",
        "purchase_completed",
    ]

    def get_overall_funnel(self) -> pd.DataFrame:
        """Calculate aggregate conversion funnel stage counts, conversions, and drop-offs.

        Returns:
            DataFrame with columns [stage, unique_sessions, stage_conversion_rate, cumulative_conversion_rate, drop_off_rate]
        """
        sql = """
        SELECT
            event_type,
            COUNT(DISTINCT session_id) as unique_sessions
        FROM fct_events_clickstream
        GROUP BY event_type
        """
        df_raw = self.query(sql)
        stage_counts = dict(zip(df_raw["event_type"], df_raw["unique_sessions"])) if not df_raw.empty else {}

        records = []
        top_of_funnel = stage_counts.get(self.FUNNEL_STAGES[0], 0)
        prev_count = top_of_funnel

        for idx, stage in enumerate(self.FUNNEL_STAGES):
            count = stage_counts.get(stage, 0)
            stage_cr = self.calc_rate(count, prev_count) if idx > 0 else 100.0
            cum_cr = self.calc_rate(count, top_of_funnel)
            drop_off = round(100.0 - stage_cr, 2) if idx > 0 else 0.0

            records.append({
                "stage_order": idx + 1,
                "stage": stage,
                "unique_sessions": count,
                "stage_conversion_rate": stage_cr,
                "cumulative_conversion_rate": cum_cr,
                "drop_off_rate": drop_off,
            })
            prev_count = count

        return pd.DataFrame(records)

    def get_funnel_by_dimension(self, dimension: str = "device_type") -> pd.DataFrame:
        """Break down funnel conversion across devices (mobile/desktop/tablet) or traffic sources."""
        valid_dims = ["device_type", "traffic_source"]
        if dimension not in valid_dims:
            raise ValueError(f"Invalid dimension '{dimension}'. Choose from {valid_dims}")

        sql = f"""
        SELECT
            {dimension},
            event_type,
            COUNT(DISTINCT session_id) as sessions
        FROM fct_events_clickstream
        WHERE {dimension} IS NOT NULL
        GROUP BY {dimension}, event_type
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame(columns=[dimension, "stage", "sessions", "stage_conversion_rate"])

        results = []
        for dim_val, group in df.groupby(dimension):
            grp_counts = dict(zip(group["event_type"], group["sessions"]))
            top = grp_counts.get(self.FUNNEL_STAGES[0], 0)
            prev = top
            for idx, stage in enumerate(self.FUNNEL_STAGES):
                cnt = grp_counts.get(stage, 0)
                stage_cr = self.calc_rate(cnt, prev) if idx > 0 else 100.0
                cum_cr = self.calc_rate(cnt, top)
                results.append({
                    dimension: dim_val,
                    "stage_order": idx + 1,
                    "stage": stage,
                    "sessions": cnt,
                    "stage_conversion_rate": stage_cr,
                    "cumulative_conversion_rate": cum_cr,
                })
                prev = cnt

        return pd.DataFrame(results)

    def get_cart_abandonment_metrics(self) -> dict[str, MetricResult]:
        """Compute Cart Abandonment Rate and Checkout Abandonment Rate."""
        funnel_df = self.get_overall_funnel()
        counts = dict(zip(funnel_df["stage"], funnel_df["unique_sessions"]))

        cart_sessions = counts.get("add_to_cart", 0)
        checkout_sessions = counts.get("checkout_started", 0)
        purchase_sessions = counts.get("purchase_completed", 0)

        # Cart abandonment: added to cart but did not purchase
        abandoned_carts = max(0, cart_sessions - purchase_sessions)
        cart_abandon_rate = self.calc_rate(abandoned_carts, cart_sessions)

        # Checkout abandonment: started checkout but did not purchase
        abandoned_checkouts = max(0, checkout_sessions - purchase_sessions)
        checkout_abandon_rate = self.calc_rate(abandoned_checkouts, checkout_sessions)

        return {
            "cart_abandonment_rate": MetricResult(
                name="Cart Abandonment Rate",
                value=cart_abandon_rate,
                formatted_value=f"{cart_abandon_rate:.1f}%",
                numerator=abandoned_carts,
                denominator=cart_sessions,
                unit="%",
                provenance="synthetic",
                notes="Percentage of sessions with Add to Cart that did not complete Purchase.",
            ),
            "checkout_abandonment_rate": MetricResult(
                name="Checkout Abandonment Rate",
                value=checkout_abandon_rate,
                formatted_value=f"{checkout_abandon_rate:.1f}%",
                numerator=abandoned_checkouts,
                denominator=checkout_sessions,
                unit="%",
                provenance="synthetic",
                notes="Percentage of sessions with Checkout Started that did not complete Purchase.",
            ),
        }
