"""Catalog quality, completeness, and merchandising distribution analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class CatalogAnalytics(BaseAnalytics):
    """Analyzes product catalog metadata, category distributions, completeness, and data quality scores."""

    REQUIRED_ATTRIBUTES = [
        "gender",
        "master_category",
        "sub_category",
        "article_type",
        "base_colour",
        "season",
        "usage",
        "product_display_name",
    ]

    def get_category_distribution(self) -> pd.DataFrame:
        """Get product count and percentage distribution by master and sub-category."""
        sql = """
        SELECT
            master_category,
            sub_category,
            COUNT(*) as product_count
        FROM dim_products
        GROUP BY master_category, sub_category
        ORDER BY product_count DESC
        """
        df = self.query(sql)
        total_prods = df["product_count"].sum() if not df.empty else 0
        df["share_percentage"] = df["product_count"].apply(
            lambda cnt: self.calc_rate(cnt, total_prods)
        )
        return df

    def get_catalog_completeness_summary(self) -> dict[str, Any]:
        """Audit missing product attributes, duplicate records, and average data quality score."""
        sql = """
        SELECT
            product_id,
            product_display_name,
            master_category,
            sub_category,
            article_type,
            base_colour,
            season,
            usage,
            catalog_completeness_score
        FROM dim_products
        """
        df = self.query(sql)
        if df.empty:
            return {
                "total_products": MetricResult("Total Products", 0, "0", unit="products"),
                "average_completeness_score": MetricResult("Average Completeness Score", 0.0, "0.0%", unit="%"),
                "missing_attributes_by_field": pd.DataFrame(),
                "incomplete_skus": pd.DataFrame(),
            }

        total_prods = len(df)
        avg_score = round(float(df["catalog_completeness_score"].mean()), 1)

        # Attribute missingness audit
        missing_records = []
        for attr in ["season", "usage", "base_colour", "article_type", "sub_category"]:
            if attr in df.columns:
                null_or_unknown = df[df[attr].isna() | df[attr].isin(["Unknown", "None", "nan", ""])].shape[0]
                missing_records.append({
                    "attribute": attr,
                    "missing_count": null_or_unknown,
                    "missing_percentage": self.calc_rate(null_or_unknown, total_prods),
                })
        missing_df = pd.DataFrame(missing_records).sort_values(by="missing_count", ascending=False)

        # Incomplete SKUs (< 85% completeness score)
        incomplete_skus = df[df["catalog_completeness_score"] < 85].copy()

        return {
            "total_products": MetricResult(
                name="Total Catalog Products",
                value=total_prods,
                formatted_value=f"{total_prods:,}",
                unit="SKUs",
                provenance="observed",
                notes="Active fashion merchandise listings.",
            ),
            "average_completeness_score": MetricResult(
                name="Average Catalog Completeness",
                value=avg_score,
                formatted_value=f"{avg_score:.1f}%",
                unit="%",
                provenance="reconciled",
                notes="Percentage of mandatory attributes fully populated across all SKUs.",
            ),
            "missing_attributes_by_field": missing_df,
            "incomplete_skus": incomplete_skus,
        }
