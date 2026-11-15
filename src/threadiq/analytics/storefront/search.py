"""Search and discovery analytics for ThreadIQ."""

from typing import Any

import pandas as pd

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult


class SearchAnalytics(BaseAnalytics):
    """Analyzes search query volumes, zero-result frequencies, and search conversion funnels."""

    def get_popular_queries(self, limit: int = 10) -> pd.DataFrame:
        """Get the most frequent search terms with click-through and zero-result metrics."""
        sql = """
        SELECT
            search_term,
            COUNT(*) as total_searches,
            SUM(zero_result_flag) as zero_result_count,
            COUNT(clicked_product_id) as clicks,
            ROUND(AVG(result_count), 1) as avg_results_returned
        FROM fct_search_queries
        GROUP BY search_term
        ORDER BY total_searches DESC
        LIMIT :limit
        """
        df = self.query(sql, {"limit": limit})
        if df.empty:
            return pd.DataFrame(columns=["search_term", "total_searches", "zero_result_count", "clicks", "click_through_rate"])

        df["click_through_rate"] = df.apply(
            lambda r: self.calc_rate(r["clicks"], r["total_searches"]), axis=1
        )
        return df

    def get_search_funnel_conversion(self) -> dict[str, MetricResult]:
        """Compute Search-to-View, Search-to-Cart, and Search-to-Purchase conversion rates."""
        # 1. Total sessions that performed a search
        sql_search_sessions = """
        SELECT COUNT(DISTINCT session_id) as cnt
        FROM fct_search_queries
        """
        search_sessions = int(self.query(sql_search_sessions).iloc[0]["cnt"])

        # 2. Search sessions that clicked or viewed a product
        sql_search_views = """
        SELECT COUNT(DISTINCT q.session_id) as cnt
        FROM fct_search_queries q
        JOIN fct_events_clickstream e ON q.session_id = e.session_id
        WHERE e.event_type = 'product_detail_view'
        """
        search_views = int(self.query(sql_search_views).iloc[0]["cnt"])

        # 3. Search sessions that added to cart
        sql_search_carts = """
        SELECT COUNT(DISTINCT q.session_id) as cnt
        FROM fct_search_queries q
        JOIN fct_events_clickstream e ON q.session_id = e.session_id
        WHERE e.event_type = 'add_to_cart'
        """
        search_carts = int(self.query(sql_search_carts).iloc[0]["cnt"])

        # 4. Search sessions that completed purchase
        sql_search_purchases = """
        SELECT COUNT(DISTINCT q.session_id) as cnt
        FROM fct_search_queries q
        JOIN fct_events_clickstream e ON q.session_id = e.session_id
        WHERE e.event_type = 'purchase_completed'
        """
        search_purchases = int(self.query(sql_search_purchases).iloc[0]["cnt"])

        return {
            "search_to_view_rate": MetricResult(
                name="Search-to-View Conversion",
                value=self.calc_rate(search_views, search_sessions),
                formatted_value=f"{self.calc_rate(search_views, search_sessions):.1f}%",
                numerator=search_views,
                denominator=search_sessions,
                unit="%",
                provenance="synthetic",
                notes="Sessions with search that proceeded to view product details.",
            ),
            "search_to_cart_rate": MetricResult(
                name="Search-to-Cart Conversion",
                value=self.calc_rate(search_carts, search_sessions),
                formatted_value=f"{self.calc_rate(search_carts, search_sessions):.1f}%",
                numerator=search_carts,
                denominator=search_sessions,
                unit="%",
                provenance="synthetic",
                notes="Sessions with search that resulted in Add to Cart.",
            ),
            "search_to_purchase_rate": MetricResult(
                name="Search-to-Purchase Conversion",
                value=self.calc_rate(search_purchases, search_sessions),
                formatted_value=f"{self.calc_rate(search_purchases, search_sessions):.1f}%",
                numerator=search_purchases,
                denominator=search_sessions,
                unit="%",
                provenance="synthetic",
                notes="Sessions with search that converted to Purchase.",
            ),
        }

    def get_zero_result_rate(self) -> MetricResult:
        """Calculate the proportion of search queries that yielded zero results."""
        sql = """
        SELECT
            COUNT(*) as total_queries,
            SUM(zero_result_flag) as zero_result_queries
        FROM fct_search_queries
        """
        df = self.query(sql)
        tot = int(df.iloc[0]["total_queries"]) if not df.empty else 0
        zero_res = int(df.iloc[0]["zero_result_queries"]) if not df.empty else 0
        rate = self.calc_rate(zero_res, tot)

        return MetricResult(
            name="Zero-Result Search Rate",
            value=rate,
            formatted_value=f"{rate:.1f}%",
            numerator=zero_res,
            denominator=tot,
            unit="%",
            provenance="synthetic",
            notes="Percentage of customer searches returning zero catalog matches.",
        )

    def get_high_impression_low_engagement_products(self, threshold_impressions: int = 5, max_ctr: float = 20.0) -> pd.DataFrame:
        """Identify catalog items with high search/browse impressions but poor click-through engagement."""
        sql = """
        SELECT
            p.product_id,
            p.product_display_name,
            p.master_category,
            p.sub_category,
            p.price_reference,
            COUNT(CASE WHEN e.event_type = 'homepage_impression' OR e.event_type = 'category_page_view' THEN 1 END) as impressions,
            COUNT(CASE WHEN e.event_type = 'product_detail_view' THEN 1 END) as detail_views,
            COUNT(CASE WHEN e.event_type = 'add_to_cart' THEN 1 END) as cart_adds
        FROM dim_products p
        LEFT JOIN fct_events_clickstream e ON p.product_id = e.product_id
        GROUP BY p.product_id, p.product_display_name, p.master_category, p.sub_category, p.price_reference
        """
        df = self.query(sql)
        if df.empty:
            return pd.DataFrame()

        df["view_ctr"] = df.apply(lambda r: self.calc_rate(r["detail_views"], r["impressions"]), axis=1)
        low_eng = df[(df["impressions"] >= threshold_impressions) & (df["view_ctr"] <= max_ctr)].copy()
        return low_eng.sort_values(by="impressions", ascending=False)
