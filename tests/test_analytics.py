"""Unit and integration tests for ThreadIQ Complete Product Analytics modules."""

from pathlib import Path

import pandas as pd
import pytest

from src.threadiq.analytics.common.base import BaseAnalytics, MetricResult
from src.threadiq.analytics.inbound import (
    CatalogAnalytics,
    InventoryAnalytics,
    PricingPromotionsAnalytics,
    ReplenishmentAnalytics,
)
from src.threadiq.analytics.outbound import (
    CancellationReturnAnalytics,
    DeliveryPerformanceAnalytics,
    FulfillmentAnalytics,
    OperationalInsightsAnalytics,
)
from src.threadiq.analytics.storefront import (
    CustomerAnalytics,
    FunnelAnalytics,
    ProductPerformanceAnalytics,
    SearchAnalytics,
)
from src.threadiq.data.loaders import get_db_engine


@pytest.fixture(scope="module")
def db_engine():
    """Fixture providing database engine connected to data/threadiq.db."""
    return get_db_engine()


# ---------------------------------------------------------------------------
# 1. STOREFRONT PRODUCT ANALYTICS TESTS
# ---------------------------------------------------------------------------

def test_storefront_funnel_calculations(db_engine):
    """Test funnel stage counts, monotonic ordering, and division-by-zero protection."""
    analytics = FunnelAnalytics(engine=db_engine)
    df_funnel = analytics.get_overall_funnel()

    assert not df_funnel.empty
    assert len(df_funnel) == len(FunnelAnalytics.FUNNEL_STAGES)
    assert list(df_funnel.columns) == [
        "stage_order", "stage", "unique_sessions",
        "stage_conversion_rate", "cumulative_conversion_rate", "drop_off_rate"
    ]

    # First stage should be 100% conversion
    assert df_funnel.iloc[0]["stage_conversion_rate"] == 100.0
    assert df_funnel.iloc[0]["drop_off_rate"] == 0.0

    # Ensure all rates are valid numbers between 0 and 100
    for _, row in df_funnel.iterrows():
        assert 0.0 <= row["cumulative_conversion_rate"] <= 100.0
        assert 0.0 <= row["stage_conversion_rate"] <= 100.0


def test_storefront_cart_abandonment(db_engine):
    """Test cart and checkout abandonment rate calculation."""
    analytics = FunnelAnalytics(engine=db_engine)
    metrics = analytics.get_cart_abandonment_metrics()

    assert "cart_abandonment_rate" in metrics
    assert "checkout_abandonment_rate" in metrics
    cart_rate = metrics["cart_abandonment_rate"].value
    assert isinstance(cart_rate, float)
    assert 0.0 <= cart_rate <= 100.0


def test_search_and_discovery_analytics(db_engine):
    """Test popular search queries, search conversion funnel, and zero-result search rate."""
    analytics = SearchAnalytics(engine=db_engine)

    # 1. Popular queries
    df_queries = analytics.get_popular_queries(limit=5)
    assert not df_queries.empty
    assert "search_term" in df_queries.columns
    assert "click_through_rate" in df_queries.columns

    # 2. Search funnels
    search_metrics = analytics.get_search_funnel_conversion()
    assert "search_to_view_rate" in search_metrics
    assert "search_to_cart_rate" in search_metrics
    assert "search_to_purchase_rate" in search_metrics

    # 3. Zero result rate
    zero_res = analytics.get_zero_result_rate()
    assert 0.0 <= zero_res.value <= 100.0


def test_product_performance_analytics(db_engine):
    """Test product-level and category-level commercial and conversion aggregations."""
    analytics = ProductPerformanceAnalytics(engine=db_engine)
    df_prod = analytics.get_product_performance_table()

    assert not df_prod.empty
    assert "product_id" in df_prod.columns
    assert "revenue" in df_prod.columns
    assert "units_sold" in df_prod.columns
    assert "add_to_cart_rate" in df_prod.columns
    assert "purchase_conversion_rate" in df_prod.columns

    # Revenue must be non-negative
    assert (df_prod["revenue"] >= 0.0).all()

    # Category performance
    df_cat = analytics.get_category_performance_summary()
    assert not df_cat.empty
    assert "total_revenue" in df_cat.columns
    assert "total_units_sold" in df_cat.columns
    assert "category_conversion_rate" in df_cat.columns


def test_customer_analytics_and_cohorts(db_engine):
    """Test AOV, repeat purchase rates, cohorts, and RFM segmentation."""
    analytics = CustomerAnalytics(engine=db_engine)

    # 1. Repeat purchase metrics
    rep_metrics = analytics.get_repeat_purchase_metrics()
    assert rep_metrics["total_unique_customers"].value > 0
    assert 0.0 <= rep_metrics["repeat_purchase_rate"].value <= 100.0

    # 2. AOV
    aov = analytics.get_average_order_value()
    assert aov.value > 0.0

    # 3. Cohort retention
    df_cohort = analytics.get_monthly_cohort_retention()
    assert not df_cohort.empty
    assert "cohort_month" in df_cohort.columns
    assert "cohort_size" in df_cohort.columns

    # 4. RFM segmentation
    df_rfm = analytics.get_rfm_customer_segments()
    assert not df_rfm.empty
    assert "segment" in df_rfm.columns
    assert "monetary_value" in df_rfm.columns


# ---------------------------------------------------------------------------
# 2. INBOUND SUPPLY CHAIN ANALYTICS TESTS
# ---------------------------------------------------------------------------

def test_catalog_analytics(db_engine):
    """Test catalog category distribution and completeness scoring."""
    analytics = CatalogAnalytics(engine=db_engine)

    # 1. Category distribution
    df_cat = analytics.get_category_distribution()
    assert not df_cat.empty
    assert df_cat["share_percentage"].sum() == pytest.approx(100.0, abs=1.0)

    # 2. Catalog completeness
    summary = analytics.get_catalog_completeness_summary()
    assert summary["total_products"].value > 0
    assert 0.0 <= summary["average_completeness_score"].value <= 100.0
    assert not summary["missing_attributes_by_field"].empty


def test_inventory_analytics_and_stockouts(db_engine):
    """Test daily stock availability, stockout frequency, and Days of Cover (DoC)."""
    analytics = InventoryAnalytics(engine=db_engine)

    # 1. Stockout summary
    so_summary = analytics.get_stockout_summary()
    assert 0.0 <= so_summary["stockout_rate"].value <= 100.0
    assert so_summary["in_stock_availability_rate"].value == pytest.approx(
        100.0 - so_summary["stockout_rate"].value, abs=0.1
    )
    assert so_summary["average_days_of_cover"].value >= 0.0

    # 2. High demand vs slow moving
    high_dem, slow_mov = analytics.get_high_demand_vs_slow_moving_skus()
    assert isinstance(high_dem, pd.DataFrame)
    assert isinstance(slow_mov, pd.DataFrame)


def test_pricing_and_promotions_analytics(db_engine):
    """Test price distribution and promotion campaign analytics."""
    analytics = PricingPromotionsAnalytics(engine=db_engine)

    # 1. Price distribution
    df_pricing = analytics.get_price_distribution_by_category()
    assert not df_pricing.empty
    assert (df_pricing["min_price"] <= df_pricing["median_price"]).all()
    assert (df_pricing["median_price"] <= df_pricing["max_price"]).all()

    # 2. Promotions summary
    promo_sum = analytics.get_promotion_summary()
    assert promo_sum["total_promotions"].value > 0
    assert 0.0 < promo_sum["avg_discount_depth"].value <= 70.0


def test_replenishment_recommendations(db_engine):
    """Test heuristic replenishment orders, column contracts, and markdown candidates."""
    analytics = ReplenishmentAnalytics(engine=db_engine)

    # Replenishment
    df_reorder = analytics.get_replenishment_recommendations(max_doc_threshold=30.0)
    assert isinstance(df_reorder, pd.DataFrame)
    if not df_reorder.empty:
        assert "current_stock" in df_reorder.columns
        assert "days_of_cover" in df_reorder.columns
        assert "urgency_level" in df_reorder.columns
        assert "suggested_reorder_units" in df_reorder.columns

    # Urgency classification business rules test
    assert "CRITICAL" in analytics.classify_urgency(5.0)
    assert "HIGH" in analytics.classify_urgency(10.0)
    assert "MEDIUM" in analytics.classify_urgency(20.0)
    assert "NORMAL" in analytics.classify_urgency(40.0)
    assert analytics.classify_urgency(None) == "UNAVAILABLE"

    # Catalog priorities
    df_enrich = analytics.get_catalog_enrichment_priorities(min_completeness=100)
    assert isinstance(df_enrich, pd.DataFrame)


# ---------------------------------------------------------------------------
# 3. OUTBOUND SUPPLY CHAIN ANALYTICS TESTS
# ---------------------------------------------------------------------------

def test_fulfillment_analytics(db_engine):
    """Test order fulfillment lifecycle funnel and status distribution."""
    analytics = FulfillmentAnalytics(engine=db_engine)
    res = analytics.get_order_fulfillment_funnel()

    assert res["orders_placed"].value >= res["orders_approved"].value
    assert not res["status_distribution"].empty
    assert "order_status" in res["status_distribution"].columns

    # Direct order status distribution method test
    status_df = analytics.get_order_status_distribution()
    assert isinstance(status_df, pd.DataFrame)
    assert not status_df.empty
    assert list(status_df.columns) == ["order_status", "order_count", "percentage"]


def test_delivery_performance_analytics(db_engine):
    """Test transit duration, on-time delivery rate, and regional breakdowns."""
    analytics = DeliveryPerformanceAnalytics(engine=db_engine)

    # 1. SLA metrics
    sla = analytics.get_delivery_sla_metrics()
    assert 0.0 <= sla["on_time_delivery_rate"].value <= 100.0
    assert 0.0 <= sla["late_delivery_rate"].value <= 100.0
    assert sla["average_delivery_time"].value >= 0.0

    # 2. Regional breakdown
    df_reg = analytics.get_regional_delivery_performance()
    assert not df_reg.empty
    assert "destination_state" in df_reg.columns
    assert "on_time_rate" in df_reg.columns
    assert "avg_transit_days" in df_reg.columns
    assert "average_transit_days" in df_reg.columns


def test_cancellation_and_return_analytics(db_engine):
    """Test cancellation rate, fashion return reasons, and category return patterns."""
    analytics = CancellationReturnAnalytics(engine=db_engine)

    # 1. Rates
    rates = analytics.get_cancellation_and_return_rates()
    assert 0.0 <= rates["order_cancellation_rate"].value <= 100.0
    assert 0.0 <= rates["item_return_rate"].value <= 100.0

    # 2. Reasons
    df_reasons = analytics.get_return_reasons_breakdown()
    assert not df_reasons.empty
    assert "return_reason" in df_reasons.columns
    assert "refund_value_exposure" in df_reasons.columns

    # 3. Category return patterns
    df_cat_returns = analytics.get_category_return_patterns()
    assert not df_cat_returns.empty
    assert "return_rate" in df_cat_returns.columns


def test_operational_insights_waterfall(db_engine):
    """Test fulfillment duration deconstruction (order-to-dispatch vs dispatch-to-delivery)."""
    analytics = OperationalInsightsAnalytics(engine=db_engine)
    waterfall = analytics.get_fulfillment_bottleneck_waterfall()

    assert waterfall["avg_order_to_dispatch_hours"].value >= 0.0
    assert waterfall["avg_dispatch_to_delivery_hours"].value >= 0.0
    assert waterfall["primary_bottleneck"] in [
        "Last-Mile / Transit (Carrier)",
        "Warehouse / Fulfillment (Seller)",
    ]

    # Seller dispatch performance
    df_sellers = analytics.get_seller_dispatch_performance()
    assert not df_sellers.empty
    assert "seller_id" in df_sellers.columns
    assert "slow_dispatch_rate" in df_sellers.columns


# ---------------------------------------------------------------------------
# 4. EDGE CASE TESTS (Empty & Division by Zero)
# ---------------------------------------------------------------------------

def test_analytics_base_safe_rate():
    """Test division-by-zero protection in base analytics."""
    assert BaseAnalytics.calc_rate(10, 0) == 0.0
    assert BaseAnalytics.calc_rate(0, 0) == 0.0
    assert BaseAnalytics.calc_rate(5, None) == 0.0
    assert BaseAnalytics.calc_rate(10, 50) == 20.0
