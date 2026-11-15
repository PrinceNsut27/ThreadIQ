"""Page 1: Executive Overview Dashboard for ThreadIQ."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.threadiq.analytics.inbound import CatalogAnalytics, InventoryAnalytics
from src.threadiq.analytics.outbound import (
    CancellationReturnAnalytics,
    DeliveryPerformanceAnalytics,
    FulfillmentAnalytics,
)
from src.threadiq.analytics.storefront import (
    CustomerAnalytics,
    FunnelAnalytics,
    ProductPerformanceAnalytics,
)
from src.threadiq.dashboard.theme import (
    COLOR_PALETTE,
    PRIMARY_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    apply_custom_css,
    get_plotly_layout,
    render_metric_card,
)


def render(engine):
    """Render Executive Overview Page."""
    st.markdown("""
    <div class="threadiq-header">
        <h1>ThreadIQ — Executive Operations & Product Overview</h1>
        <p>Real-time cross-pillar performance diagnostics across Storefront, Inbound, and Outbound operations.</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Instantiate Analytics Engines
    cust_analytics = CustomerAnalytics(engine)
    prod_analytics = ProductPerformanceAnalytics(engine)
    funnel_analytics = FunnelAnalytics(engine)
    fulfill_analytics = FulfillmentAnalytics(engine)
    deliv_analytics = DeliveryPerformanceAnalytics(engine)
    cancel_analytics = CancellationReturnAnalytics(engine)
    inv_analytics = InventoryAnalytics(engine)

    # 2. Extract Key Performance Indicators
    aov_metric = cust_analytics.get_average_order_value()
    repeat_metrics = cust_analytics.get_repeat_purchase_metrics()
    deliv_metrics = deliv_analytics.get_delivery_sla_metrics()
    cancel_metrics = cancel_analytics.get_cancellation_and_return_rates()
    stock_metrics = inv_analytics.get_stockout_summary()
    abandon_metrics = funnel_analytics.get_cart_abandonment_metrics()

    # Query Total Revenue & Orders directly from fct_orders & fct_order_items
    try:
        with engine.connect() as conn:
            rev_df = pd.read_sql_query(
                "SELECT COUNT(DISTINCT order_id) as total_orders, "
                "COALESCE(SUM(price), 0.0) as gross_revenue FROM fct_order_items;",
                conn,
            )
            total_orders = int(rev_df.iloc[0]["total_orders"])
            gross_revenue = float(rev_df.iloc[0]["gross_revenue"])
    except Exception as e:
        total_orders = 0
        gross_revenue = 0.0

    total_customers = repeat_metrics["total_unique_customers"].value
    otd_rate = deliv_metrics["on_time_delivery_rate"].value
    cancel_rate = cancel_metrics["order_cancellation_rate"].value
    return_rate = cancel_metrics["item_return_rate"].value

    # 3. High-Level KPI Metric Deck
    st.subheader("High-Level Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            label="Gross Merchandise Value",
            value=f"${gross_revenue:,.2f}",
            sub_text="Total verified sales volume",
            provenance="observed",
        )
    with col2:
        render_metric_card(
            label="Total Orders Completed",
            value=f"{total_orders:,}",
            sub_text=f"AOV: {aov_metric.formatted_value}",
            provenance="observed",
        )
    with col3:
        render_metric_card(
            label="Unique Customers",
            value=f"{total_customers:,}",
            sub_text=f"Repeat rate: {repeat_metrics['repeat_purchase_rate'].formatted_value}",
            provenance="observed",
        )
    with col4:
        render_metric_card(
            label="On-Time Delivery (OTD%)",
            value=f"{otd_rate:.1f}%",
            sub_text=f"Avg delivery: {deliv_metrics['average_delivery_time'].formatted_value}",
            provenance="observed",
        )

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        render_metric_card(
            label="Cart Abandonment Rate",
            value=abandon_metrics["cart_abandonment_rate"].formatted_value,
            sub_text="High conversion leakage",
            provenance="synthetic",
        )
    with col6:
        render_metric_card(
            label="Order Cancellation Rate",
            value=f"{cancel_rate:.1f}%",
            sub_text="Pre-fulfillment aborts",
            provenance="observed",
        )
    with col7:
        render_metric_card(
            label="Apparel Item Return Rate",
            value=f"{return_rate:.1f}%",
            sub_text="Primary reverse logistics load",
            provenance="reconciled",
        )
    with col8:
        render_metric_card(
            label="Catalog In-Stock Rate",
            value=stock_metrics["in_stock_availability_rate"].formatted_value,
            sub_text=f"Avg DoC: {stock_metrics['average_days_of_cover'].formatted_value}",
            provenance="synthetic",
        )

    st.markdown("---")

    # 4. Interactive Trend & Distribution Charts
    chart_col1, chart_col2 = st.columns([6, 4])

    with chart_col1:
        st.subheader("Category Revenue vs. Return Value Exposure")
        cat_df = prod_analytics.get_category_performance_summary()
        ret_cat_df = cancel_analytics.get_category_return_patterns()

        if not cat_df.empty:
            merged_cat = pd.merge(
                cat_df, ret_cat_df, on="sub_category", how="left"
            ).fillna(0.0)

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=merged_cat["sub_category"],
                y=merged_cat["total_revenue"],
                name="Gross Revenue ($)",
                marker_color=PRIMARY_COLOR,
            ))
            fig_bar.add_trace(go.Bar(
                x=merged_cat["sub_category"],
                y=merged_cat["return_value_exposure"],
                name="Return Refund Exposure ($)",
                marker_color="#DC2626",
            ))
            layout = get_plotly_layout(
                title="Category Revenue vs. Return Financial Exposure", height=380
            )
            fig_bar.update_layout(**layout, barmode="group")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No category sales records found.")

    with chart_col2:
        st.subheader("Fulfillment Order Status Breakdown")
        status_df = fulfill_analytics.get_order_status_distribution()
        if not status_df.empty:
            fig_donut = px.pie(
                status_df,
                values="order_count",
                names="order_status",
                hole=0.55,
                color_discrete_sequence=COLOR_PALETTE,
            )
            layout = get_plotly_layout(title="Order Status Distribution", height=380)
            fig_donut.update_layout(**layout)
            fig_donut.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No fulfillment records available.")

    # 5. Top Commercial Fashion SKUs
    st.subheader("Top Commercial Product Performance")
    prod_table = prod_analytics.get_product_performance_table()
    if not prod_table.empty:
        display_prod = prod_table[[
            "product_id", "product_display_name", "sub_category",
            "units_sold", "revenue", "average_selling_price",
            "add_to_cart_rate", "purchase_conversion_rate"
        ]].copy()
        display_prod.columns = [
            "SKU ID", "Product Display Name", "Sub-Category",
            "Units Sold", "Gross Revenue ($)", "ASP ($)",
            "Cart Rate (%)", "Conversion Rate (%)"
        ]
        st.dataframe(
            display_prod.sort_values(by="Gross Revenue ($)", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No product performance data available.")
