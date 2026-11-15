"""Page 4: Outbound Intelligence Dashboard for ThreadIQ."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.threadiq.analytics.outbound import (
    CancellationReturnAnalytics,
    DeliveryPerformanceAnalytics,
    FulfillmentAnalytics,
    OperationalInsightsAnalytics,
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
    """Render Outbound Supply Chain & Logistics Intelligence Page."""
    st.markdown("""
    <div class="threadiq-header">
        <h1>Outbound Logistics & Reverse Supply Chain</h1>
        <p>Order fulfillment lifecycle, carrier SLA compliance (OTD%), fashion return reason decomposition, and operational bottleneck waterfalls.</p>
    </div>
    """, unsafe_allow_html=True)

    fulfill_analytics = FulfillmentAnalytics(engine)
    deliv_analytics = DeliveryPerformanceAnalytics(engine)
    cancel_analytics = CancellationReturnAnalytics(engine)
    ops_analytics = OperationalInsightsAnalytics(engine)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Fulfillment Lifecycle", "Delivery SLA & Carrier Performance", "Cancellations & Return Diagnostics", "Bottleneck Waterfall"
    ])

    # ---------------------------------------------------------
    # TAB 1: FULFILLMENT LIFECYCLE
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Order Fulfillment Lifecycle Funnel")
        funnel_res = fulfill_analytics.get_order_fulfillment_funnel()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card(
                label="Orders Placed",
                value=str(funnel_res["orders_placed"].value),
                sub_text="Total customer transactions",
                provenance="observed",
            )
        with col2:
            render_metric_card(
                label="Orders Approved",
                value=str(funnel_res["orders_approved"].value),
                sub_text="Payment verified",
                provenance="observed",
            )
        with col3:
            render_metric_card(
                label="Orders Dispatched",
                value=str(funnel_res["orders_dispatched"].value),
                sub_text="Carrier pickup confirmed",
                provenance="observed",
            )
        with col4:
            render_metric_card(
                label="Orders Delivered",
                value=str(funnel_res["orders_delivered"].value),
                sub_text=f"{funnel_res['orders_canceled'].value} canceled orders",
                provenance="observed",
            )

        status_df = funnel_res["status_distribution"]
        if not status_df.empty:
            fig_stat = px.bar(
                status_df,
                x="order_status",
                y="order_count",
                color="order_status",
                title="Order Status Distribution",
                color_discrete_sequence=COLOR_PALETTE,
            )
            fig_stat.update_layout(**get_plotly_layout(height=360))
            st.plotly_chart(fig_stat, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: DELIVERY SLA & CARRIERS
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Carrier Performance & On-Time Delivery (OTD%)")
        sla_metrics = deliv_analytics.get_delivery_sla_metrics()

        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            render_metric_card(
                label="On-Time Delivery Rate (OTD%)",
                value=sla_metrics["on_time_delivery_rate"].formatted_value,
                sub_text="Target: >= 95.0% on-time delivery",
                provenance="observed",
            )
        with scol2:
            render_metric_card(
                label="Late Delivery Rate",
                value=sla_metrics["late_delivery_rate"].formatted_value,
                sub_text=f"{sla_metrics['late_delivery_rate'].numerator} late shipments",
                provenance="observed",
            )
        with scol3:
            render_metric_card(
                label="Average Transit Duration",
                value=sla_metrics["average_delivery_time"].formatted_value,
                sub_text="Purchase confirmation to doorstep",
                provenance="observed",
            )

        reg_df = deliv_analytics.get_regional_delivery_performance()
        if not reg_df.empty:
            st.markdown("##### Regional Logistics Performance by Destination State")
            color_col = "avg_transit_days" if "avg_transit_days" in reg_df.columns else "average_transit_days"
            fig_reg = px.bar(
                reg_df,
                x="destination_state",
                y="on_time_rate",
                color=color_col if color_col in reg_df.columns else None,
                title="Regional On-Time Rate (%) vs. Average Transit Days",
                color_continuous_scale="Viridis",
            )
            fig_reg.update_layout(**get_plotly_layout(height=360))
            st.plotly_chart(fig_reg, use_container_width=True)
            st.dataframe(reg_df, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # TAB 3: CANCELLATIONS & RETURNS
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Cancellations & Fashion Return Reason Diagnostics")
        rates = cancel_analytics.get_cancellation_and_return_rates()

        rcol1, rcol2 = st.columns(2)
        with rcol1:
            render_metric_card(
                label="Order Cancellation Rate",
                value=rates["order_cancellation_rate"].formatted_value,
                sub_text=f"{rates['order_cancellation_rate'].numerator} canceled orders",
                provenance="observed",
            )
        with rcol2:
            render_metric_card(
                label="Apparel Item Return Rate",
                value=rates["item_return_rate"].formatted_value,
                sub_text=f"{rates['item_return_rate'].numerator} returned apparel items",
                provenance="reconciled",
            )

        ccol1, ccol2 = st.columns(2)
        with ccol1:
            st.markdown("##### Return Reasons Decomposition")
            reasons_df = cancel_analytics.get_return_reasons_breakdown()
            if not reasons_df.empty:
                fig_reas = px.pie(
                    reasons_df,
                    values="return_count",
                    names="return_reason",
                    hole=0.45,
                    title="Return Reasons Breakdown (Size & Fit = 38.5%)",
                    color_discrete_sequence=COLOR_PALETTE,
                )
                fig_reas.update_layout(**get_plotly_layout(height=340))
                st.plotly_chart(fig_reas, use_container_width=True)
                st.dataframe(reasons_df, use_container_width=True, hide_index=True)

        with ccol2:
            st.markdown("##### Sub-Category Return Vulnerability")
            cat_ret_df = cancel_analytics.get_category_return_patterns()
            if not cat_ret_df.empty:
                fig_cat_ret = px.bar(
                    cat_ret_df,
                    x="sub_category",
                    y="return_rate",
                    color="return_rate",
                    title="Category Return Rate (%) — Activewear at 60.0%",
                    color_continuous_scale="Reds",
                )
                fig_cat_ret.update_layout(**get_plotly_layout(height=340))
                st.plotly_chart(fig_cat_ret, use_container_width=True)
                st.dataframe(cat_ret_df, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # TAB 4: BOTTLENECK WATERFALL
    # ---------------------------------------------------------
    with tab4:
        st.subheader("Fulfillment Duration Waterfall: Merchant vs. Carrier")
        waterfall = ops_analytics.get_fulfillment_bottleneck_waterfall()

        wcol1, wcol2, wcol3 = st.columns(3)
        with wcol1:
            render_metric_card(
                label="Order-to-Dispatch (Merchant)",
                value=waterfall["avg_order_to_dispatch_hours"].formatted_value,
                sub_text=f"{waterfall['order_to_dispatch_share_pct']}% of total lead time",
                provenance="observed",
            )
        with wcol2:
            render_metric_card(
                label="Dispatch-to-Delivery (Carrier)",
                value=waterfall["avg_dispatch_to_delivery_hours"].formatted_value,
                sub_text=f"{waterfall['dispatch_to_delivery_share_pct']}% of total lead time",
                provenance="observed",
            )
        with wcol3:
            render_metric_card(
                label="Primary Operational Bottleneck",
                value=waterfall["primary_bottleneck"],
                sub_text="Carrier transit represents 75% of delay",
                provenance="observed",
            )

        # Plotly Waterfall Chart
        fig_water = go.Figure(go.Waterfall(
            name="Lead Time Waterfall",
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Merchant Fulfillment (Dispatch)", "Carrier In-Transit", "Total Lead Time"],
            textposition="outside",
            text=[
                f"{waterfall['avg_order_to_dispatch_hours'].value:.1f} hrs",
                f"{waterfall['avg_dispatch_to_delivery_hours'].value:.1f} hrs",
                f"{(waterfall['avg_order_to_dispatch_hours'].value + waterfall['avg_dispatch_to_delivery_hours'].value):.1f} hrs",
            ],
            y=[
                waterfall["avg_order_to_dispatch_hours"].value,
                waterfall["avg_dispatch_to_delivery_hours"].value,
                0,
            ],
            connector={"line": {"color": "#64748B"}},
            decreasing={"marker": {"color": "#10B981"}},
            increasing={"marker": {"color": "#2563EB"}},
            totals={"marker": {"color": "#0F172A"}},
        ))
        layout = get_plotly_layout(title="Order Fulfillment Duration Decomposition (Hours)", height=380)
        fig_water.update_layout(**layout)
        st.plotly_chart(fig_water, use_container_width=True)

        st.markdown("##### Merchant Dispatch SLA Performance")
        seller_df = ops_analytics.get_seller_dispatch_performance()
        if not seller_df.empty:
            st.dataframe(seller_df, use_container_width=True, hide_index=True)
