"""Pricing patterns, markdown depth, and promotion analytics for ThreadIQ."""

from typing import Any

import numpy as np
import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class PricingPromotionsAnalytics(BaseAnalytics):
    """Analyzes catalog price distribution, discount depth, and promotional sales lift."""

    def get_price_distribution_by_category(self) -> pd.DataFrame:
        """Calculate min, 25th percentile, median, 75th percentile, and max pricing by category."""
        sql = """
        SELECT
            master_category,
            sub_category,
            price_reference
        FROM dim_products
        WHERE price_reference IS NOT NULL
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame()

        records = []
        for (mc, sc), group in df.groupby(["master_category", "sub_category"]):
            prices = group["price_reference"]
            records.append({
                "master_category": mc,
                "sub_category": sc,
                "sku_count": len(prices),
                "min_price": round(float(prices.min()), 2),
                "p25_price": round(float(prices.quantile(0.25)), 2),
                "median_price": round(float(prices.median()), 2),
                "p75_price": round(float(prices.quantile(0.75)), 2),
                "max_price": round(float(prices.max()), 2),
            })
        return pd.DataFrame(records).sort_values(by="median_price", ascending=False)

    def get_promotion_summary(self) -> dict[str, Any]:
        """Audit active promotion campaigns and average markdown depth."""
        sql = """
        SELECT
            promotion_id,
            product_id,
            category,
            discount_percentage,
            start_date,
            end_date,
            promotion_type
        FROM fct_promotions
        """
        df = self.query(sql)
        if df.empty:
            return {
                "total_promotions": MetricResult("Total Promotions", 0, "0", unit="campaigns"),
                "avg_discount_depth": MetricResult("Average Discount Depth", 0.0, "0.0%", unit="%"),
                "campaigns_by_type": pd.DataFrame(),
            }

        total_promos = len(df)
        avg_disc = round(float(df["discount_percentage"].mean() * 100.0), 1)

        type_breakdown = df.groupby("promotion_type").agg(
            campaign_count=("promotion_id", "count"),
            avg_discount=("discount_percentage", lambda x: round(float(x.mean() * 100.0), 1)),
        ).reset_index().sort_values(by="campaign_count", ascending=False)

        return {
            "total_promotions": MetricResult(
                name="Total Promotional Campaigns",
                value=total_promos,
                formatted_value=f"{total_promos:,}",
                unit="campaigns",
                provenance="synthetic",
                notes="Active discount campaigns across fashion catalog.",
            ),
            "avg_discount_depth": MetricResult(
                name="Average Discount Depth",
                value=avg_disc,
                formatted_value=f"{avg_disc:.1f}%",
                unit="%",
                provenance="synthetic",
                notes="Mean promotional price reduction percentage.",
            ),
            "campaigns_by_type": type_breakdown,
            "promotions_list": df,
        }
