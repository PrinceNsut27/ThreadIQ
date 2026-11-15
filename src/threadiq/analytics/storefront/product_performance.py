"""Product performance analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class ProductPerformanceAnalytics(BaseAnalytics):
    """Calculates product-level and category-level commercial and engagement metrics."""

    def get_product_performance_table(self) -> pd.DataFrame:
        """Calculate views, units sold, revenue, ASP, add-to-cart rate, and purchase conversion for all SKUs."""
        sql = """
        SELECT
            p.product_id,
            p.product_display_name,
            p.master_category,
            p.sub_category,
            p.price_reference,
            COALESCE(views.view_count, 0) as views,
            COALESCE(carts.cart_count, 0) as cart_additions,
            COALESCE(sales.units_sold, 0) as units_sold,
            COALESCE(sales.total_revenue, 0.0) as revenue
        FROM dim_products p
        LEFT JOIN (
            SELECT product_id, COUNT(*) as view_count
            FROM fct_events_clickstream
            WHERE event_type = 'product_detail_view'
            GROUP BY product_id
        ) views ON p.product_id = views.product_id
        LEFT JOIN (
            SELECT product_id, COUNT(*) as cart_count
            FROM fct_events_clickstream
            WHERE event_type = 'add_to_cart'
            GROUP BY product_id
        ) carts ON p.product_id = carts.product_id
        LEFT JOIN (
            SELECT
                i.product_id,
                COUNT(i.order_item_uid) as units_sold,
                SUM(i.price) as total_revenue
            FROM fct_order_items i
            JOIN fct_orders o ON i.order_id = o.order_id
            WHERE o.order_status NOT IN ('canceled', 'unavailable')
            GROUP BY i.product_id
        ) sales ON p.product_id = sales.product_id
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame(columns=[
                "product_id", "product_display_name", "master_category", "sub_category",
                "price_reference", "views", "cart_additions", "units_sold", "revenue",
                "average_selling_price", "add_to_cart_rate", "purchase_conversion_rate"
            ])

        # Average selling price: revenue / units_sold (or price_reference if 0 units sold)
        df["average_selling_price"] = df.apply(
            lambda r: round(r["revenue"] / r["units_sold"], 2) if r["units_sold"] > 0 else r["price_reference"],
            axis=1,
        )

        # Add to cart rate: cart_additions / views
        df["add_to_cart_rate"] = df.apply(
            lambda r: self.calc_rate(r["cart_additions"], r["views"]),
            axis=1,
        )

        # Purchase conversion rate: units_sold / views
        df["purchase_conversion_rate"] = df.apply(
            lambda r: self.calc_rate(r["units_sold"], r["views"]),
            axis=1,
        )

        return df.sort_values(by="revenue", ascending=False)

    def get_category_performance_summary(self) -> pd.DataFrame:
        """Aggregate performance metrics at the master and sub-category level."""
        df_prod = self.get_product_performance_table()
        if df_prod.empty:
            return pd.DataFrame()

        grp = df_prod.groupby(["master_category", "sub_category"]).agg(
            sku_count=("product_id", "count"),
            total_views=("views", "sum"),
            total_cart_additions=("cart_additions", "sum"),
            total_units_sold=("units_sold", "sum"),
            total_revenue=("revenue", "sum"),
        ).reset_index()

        grp["category_asp"] = grp.apply(
            lambda r: round(r["total_revenue"] / r["total_units_sold"], 2) if r["total_units_sold"] > 0 else 0.0,
            axis=1,
        )
        grp["category_add_to_cart_rate"] = grp.apply(
            lambda r: self.calc_rate(r["total_cart_additions"], r["total_views"]),
            axis=1,
        )
        grp["category_conversion_rate"] = grp.apply(
            lambda r: self.calc_rate(r["total_units_sold"], r["total_views"]),
            axis=1,
        )

        return grp.sort_values(by="total_revenue", ascending=False)
