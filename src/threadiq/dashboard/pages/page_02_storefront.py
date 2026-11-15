"""Page 2: Storefront Intelligence Dashboard for ThreadIQ."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.threadiq.analytics.storefront import (
    CustomerAnalytics,
    FunnelAnalytics,
    ProductPerformanceAnalytics,
    SearchAnalytics,
)
from src.threadiq.dashboard.theme import (
    COLOR_PALETTE,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    get_plotly_layout,
    render_metric_card,
)


def render(engine):
    """Render Storefront Product Analytics Page."""
    st.markdown("""
    <div class="threadiq-header">
        <h1>Storefront Product Intelligence</h1>
        <p>Conversion funnel friction, search effectiveness, catalog merchandising, and customer cohort retention.</p>
    </div>
    """, unsafe_allow_html=True)

    funnel_analytics = FunnelAnalytics(engine)
    search_analytics = SearchAnalytics(engine)
    prod_analytics = ProductPerformanceAnalytics(engine)
    cust_analytics = CustomerAnalytics(engine)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Conversion Funnel", "Search & Discovery", "Product & Category Performance", "Customer Cohorts & RFM"
    ])

    # ---------------------------------------------------------
    # TAB 1: CONVERSION FUNNEL
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Customer Journey Conversion Funnel")
        df_funnel = funnel_analytics.get_overall_funnel()
        abandon_metrics = funnel_analytics.get_cart_abandonment_metrics()

        col1, col2, col3 = st.columns(3)
        with col1:
            render_metric_card(
                label="End-to-End Funnel Conversion",
                value=f"{df_funnel.iloc[-1]['cumulative_conversion_rate']:.2f}%",
                sub_text="Homepage to Purchase Completed",
                provenance="synthetic",
            )
        with col2:
            render_metric_card(
                label="Cart Abandonment Rate",
                value=abandon_metrics["cart_abandonment_rate"].formatted_value,
                sub_text="Sessions with cart but no purchase",
                provenance="synthetic",
            )
        with col3:
            render_metric_card(
                label="Checkout Abandonment Rate",
                value=abandon_metrics["checkout_abandonment_rate"].formatted_value,
                sub_text="Sessions starting checkout but no purchase",
                provenance="synthetic",
            )

        if not df_funnel.empty:
            fig_funnel = go.Figure(go.Funnel(
                y=df_funnel["stage"].str.replace("_", " ").str.title(),
                x=df_funnel["unique_sessions"],
                textposition="inside",
                textinfo="value+percent previous",
                marker={"color": [
                    "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#F59E0B", "#10B981"
                ]},
            ))
            layout = get_plotly_layout(title="Full-Funnel Unique Session Progression", height=420)
            fig_funnel.update_layout(**layout)
            st.plotly_chart(fig_funnel, use_container_width=True)

            # Drop-off analysis table
            st.markdown("##### Stage Conversion & Drop-Off Telemetry")
            st.dataframe(df_funnel, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # TAB 2: SEARCH & DISCOVERY
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Search Performance & Discoverability")
        search_conv = search_analytics.get_search_funnel_conversion()
        zero_res = search_analytics.get_zero_result_rate()

        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            render_metric_card(
                label="Zero-Result Search Rate",
                value=zero_res.formatted_value,
                sub_text=f"{zero_res.numerator} failed searches out of {zero_res.denominator}",
                provenance="synthetic",
            )
        with scol2:
            render_metric_card(
                label="Search-to-View Conversion",
                value=search_conv["search_to_view_rate"].formatted_value,
                sub_text="Searches resulting in PDP views",
                provenance="synthetic",
            )
        with scol3:
            render_metric_card(
                label="Search-to-Purchase Conversion",
                value=search_conv["search_to_purchase_rate"].formatted_value,
                sub_text="Searches resulting in purchase",
                provenance="synthetic",
            )

        st.markdown("##### Popular User Search Queries & Click-Through Rates")
        df_queries = search_analytics.get_popular_queries(limit=15)
        if not df_queries.empty:
            st.dataframe(df_queries, use_container_width=True, hide_index=True)
        else:
            st.info("No search queries recorded.")

    # ---------------------------------------------------------
    # TAB 3: PRODUCT & CATEGORY PERFORMANCE
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Catalog Merchandising & Commercial Velocity")
        df_prod = prod_analytics.get_product_performance_table()
        df_cat = prod_analytics.get_category_performance_summary()

        pcol1, pcol2 = st.columns([6, 4])
        with pcol1:
            if not df_cat.empty:
                units_col = "total_units_sold" if "total_units_sold" in df_cat.columns else None
                fig_cat = px.bar(
                    df_cat,
                    x="sub_category",
                    y="total_revenue",
                    color=units_col,
                    title="Gross Revenue by Sub-Category",
                    color_continuous_scale="Blues",
                )
                fig_cat.update_layout(**get_plotly_layout(height=360))
                st.plotly_chart(fig_cat, use_container_width=True)

        with pcol2:
            if not df_cat.empty:
                units_col = "total_units_sold" if "total_units_sold" in df_cat.columns else "sku_count"
                fig_cat_pie = px.pie(
                    df_cat,
                    values=units_col,
                    names="sub_category",
                    hole=0.45,
                    title="Unit Sales Volume by Category",
                    color_discrete_sequence=COLOR_PALETTE,
                )
                fig_cat_pie.update_layout(**get_plotly_layout(height=360))
                st.plotly_chart(fig_cat_pie, use_container_width=True)

        st.markdown("##### Detailed SKU Commercial Performance")
        if not df_prod.empty:
            st.dataframe(
                df_prod.sort_values(by="revenue", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    # ---------------------------------------------------------
    # TAB 4: CUSTOMER COHORTS & RFM
    # ---------------------------------------------------------
    with tab4:
        st.subheader("Customer Lifetime Value & RFM Segmentation")
        repeat_metrics = cust_analytics.get_repeat_purchase_metrics()
        aov_metric = cust_analytics.get_average_order_value()

        ccol1, ccol2, ccol3 = st.columns(3)
        with ccol1:
            render_metric_card(
                label="Unique Customers",
                value=str(repeat_metrics["total_unique_customers"].value),
                sub_text="Distinct consumer entities",
                provenance="observed",
            )
        with ccol2:
            render_metric_card(
                label="Repeat Purchase Rate",
                value=repeat_metrics["repeat_purchase_rate"].formatted_value,
                sub_text=f"{repeat_metrics['repeat_customers_count'].value} repeat buyers",
                provenance="observed",
            )
        with ccol3:
            render_metric_card(
                label="Average Order Value",
                value=aov_metric.formatted_value,
                sub_text=f"Total: ${aov_metric.numerator:,.2f}",
                provenance="observed",
            )

        rfm_df = cust_analytics.get_rfm_customer_segments()
        if not rfm_df.empty:
            st.markdown("##### RFM Behavioral Segmentation Distribution")
            seg_counts = rfm_df["segment"].value_counts().reset_index()
            seg_counts.columns = ["Segment", "Customer Count"]

            fig_rfm = px.bar(
                seg_counts,
                x="Customer Count",
                y="Segment",
                orientation="h",
                color="Customer Count",
                color_continuous_scale="Purples",
                title="Customer Segmentation Breakdown",
            )
            fig_rfm.update_layout(**get_plotly_layout(height=320))
            st.plotly_chart(fig_rfm, use_container_width=True)

            st.dataframe(rfm_df, use_container_width=True, hide_index=True)
