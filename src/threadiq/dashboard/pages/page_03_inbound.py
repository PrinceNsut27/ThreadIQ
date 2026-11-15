"""Page 3: Inbound Intelligence Dashboard for ThreadIQ."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.threadiq.analytics.inbound import (
    CatalogAnalytics,
    InventoryAnalytics,
    PricingPromotionsAnalytics,
    ReplenishmentAnalytics,
)
from src.threadiq.dashboard.theme import (
    COLOR_PALETTE,
    PRIMARY_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    get_plotly_layout,
    render_metric_card,
)


def render(engine):
    """Render Inbound Supply Chain & Catalog Intelligence Page."""
    st.markdown("""
    <div class="threadiq-header">
        <h1>Inbound Supply Chain & Catalog Intelligence</h1>
        <p>Catalog completeness, daily warehouse inventory health, Days of Cover (DoC), replenishment, and pricing elasticity.</p>
    </div>
    """, unsafe_allow_html=True)

    catalog_analytics = CatalogAnalytics(engine)
    inv_analytics = InventoryAnalytics(engine)
    pricing_analytics = PricingPromotionsAnalytics(engine)
    replenish_analytics = ReplenishmentAnalytics(engine)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Catalog Quality & Audit", "Inventory Health & DoC", "Replenishment & Markdown Triggers", "Pricing & Promotions"
    ])

    # ---------------------------------------------------------
    # TAB 1: CATALOG QUALITY & COMPLETENESS
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Catalog Completeness & Attribute Governance")
        completeness_summary = catalog_analytics.get_catalog_completeness_summary()
        avg_score = completeness_summary["average_completeness_score"].value

        col1, col2, col3 = st.columns(3)
        with col1:
            render_metric_card(
                label="Average Catalog Completeness",
                value=f"{avg_score:.1f}%",
                sub_text="Target: 100.0% attribute completeness",
                provenance="reconciled",
            )
        with col2:
            render_metric_card(
                label="Active Catalog Products",
                value=str(completeness_summary["total_products"].value),
                sub_text="Total active fashion SKUs",
                provenance="observed",
            )
        with col3:
            missing_df = completeness_summary["missing_attributes_by_field"]
            missing_count = int(missing_df["missing_count"].sum()) if not missing_df.empty else 0
            render_metric_card(
                label="Total Missing Attributes",
                value=str(missing_count),
                sub_text="Across season, usage & attributes",
                provenance="reconciled",
            )

        cat_col1, cat_col2 = st.columns([5, 5])
        with cat_col1:
            st.markdown("##### Attribute Completeness Audit")
            if not missing_df.empty:
                fig_miss = px.bar(
                    missing_df,
                    x="attribute",
                    y="missing_percentage",
                    title="Missing Attribute Percentage by Field",
                    color="missing_percentage",
                    color_continuous_scale="Reds",
                )
                fig_miss.update_layout(**get_plotly_layout(height=340))
                st.plotly_chart(fig_miss, use_container_width=True)

        with cat_col2:
            st.markdown("##### Category Distribution")
            df_dist = catalog_analytics.get_category_distribution()
            if not df_dist.empty:
                fig_dist = px.pie(
                    df_dist,
                    values="product_count",
                    names="sub_category",
                    hole=0.45,
                    title="Product Catalog Category Share",
                    color_discrete_sequence=COLOR_PALETTE,
                )
                fig_dist.update_layout(**get_plotly_layout(height=340))
                st.plotly_chart(fig_dist, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: INVENTORY HEALTH & DAYS OF COVER (DoC)
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Daily Inventory Availability & Stockout Diagnostics")
        inv_summary = inv_analytics.get_stockout_summary()

        icol1, icol2, icol3 = st.columns(3)
        with icol1:
            render_metric_card(
                label="In-Stock Availability Rate",
                value=inv_summary["in_stock_availability_rate"].formatted_value,
                sub_text="Target: >= 98.0% daily availability",
                provenance="synthetic",
            )
        with icol2:
            render_metric_card(
                label="Stockout Rate (SKU-Days)",
                value=inv_summary["stockout_rate"].formatted_value,
                sub_text=f"{inv_summary['stockout_rate'].numerator} zero-stock SKU days",
                provenance="synthetic",
            )
        with icol3:
            render_metric_card(
                label="Average Days of Cover",
                value=inv_summary["average_days_of_cover"].formatted_value,
                sub_text="Target Window: 14 to 45 Days",
                provenance="synthetic",
            )

        high_dem, slow_mov = inv_analytics.get_high_demand_vs_slow_moving_skus()
        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.markdown("##### High-Velocity SKUs (Critical Stockout Vulnerability)")
            if not high_dem.empty:
                st.dataframe(high_dem, use_container_width=True, hide_index=True)
            else:
                st.info("No immediate high-demand stockout risks detected.")

        with mcol2:
            st.markdown("##### Slow-Moving SKUs (Working Capital Overhang > 60 DoC)")
            if not slow_mov.empty:
                st.dataframe(slow_mov, use_container_width=True, hide_index=True)
            else:
                st.info("No overstocked inventory found.")

    # ---------------------------------------------------------
    # TAB 3: REPLENISHMENT & MARKDOWN RECOMMENDATIONS
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Algorithmic Inbound Decision Support")
        reorder_df = replenish_analytics.get_replenishment_recommendations(max_doc_threshold=30.0)

        st.markdown("##### Urgent Purchase Order Recommendations (DoC <= 30 Days)")
        if not reorder_df.empty:
            desired_cols = [
                "product_id", "product_display_name", "sub_category",
                "current_stock", "daily_sales_velocity", "days_of_cover",
                "urgency_level", "suggested_reorder_units"
            ]
            available_cols = [c for c in desired_cols if c in reorder_df.columns]
            st.dataframe(
                reorder_df[available_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("All inventory is currently above the 30-day safety reorder threshold.")

        st.markdown("##### Catalog Enrichment Priorities (Missing Attributes)")
        enrich_df = replenish_analytics.get_catalog_enrichment_priorities(min_completeness=100)
        if not enrich_df.empty:
            st.dataframe(enrich_df, use_container_width=True, hide_index=True)
        else:
            st.success("All active catalog listings have 100% attribute completeness.")

    # ---------------------------------------------------------
    # TAB 4: PRICING & PROMOTIONS
    # ---------------------------------------------------------
    with tab4:
        st.subheader("Pricing Structure & Promotional Campaigns")
        promo_summary = pricing_analytics.get_promotion_summary()

        pcol1, pcol2 = st.columns(2)
        with pcol1:
            render_metric_card(
                label="Active Promotional Campaigns",
                value=str(promo_summary["total_promotions"].value),
                sub_text="Across fashion merchandise catalog",
                provenance="synthetic",
            )
        with pcol2:
            render_metric_card(
                label="Average Promotional Discount Depth",
                value=promo_summary["avg_discount_depth"].formatted_value,
                sub_text="Flash Sales average 30.0% discount",
                provenance="synthetic",
            )

        st.markdown("##### Price Distribution Quartiles by Sub-Category")
        price_dist_df = pricing_analytics.get_price_distribution_by_category()
        if not price_dist_df.empty:
            st.dataframe(price_dist_df, use_container_width=True, hide_index=True)

        st.markdown("##### Active Campaign Breakdown by Type")
        campaign_types = promo_summary["campaigns_by_type"]
        if not campaign_types.empty:
            fig_promo = px.bar(
                campaign_types,
                x="promotion_type",
                y="campaign_count",
                color="avg_discount",
                title="Promotional Mix & Average Discount Depth",
                color_continuous_scale="Viridis",
            )
            fig_promo.update_layout(**get_plotly_layout(height=340))
            st.plotly_chart(fig_promo, use_container_width=True)
