"""Page 7: Product Insights & Strategic Recommendations Dashboard."""

import streamlit as st

from src.threadiq.dashboard.theme import (
    PRIMARY_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    render_metric_card,
)


def render(engine):
    """Render Product Insights & Decision Support Page."""
    st.markdown("""
    <div class="threadiq-header">
        <h1>Product Insights & Strategic Interventions</h1>
        <p>Evidence-backed product opportunities with verified metrics, root-cause hypotheses, and PRD solution mappings.</p>
    </div>
    """, unsafe_allow_html=True)

    pillar_filter = st.selectbox(
        "Filter Insights by Product Pillar:",
        ["All Pillars", "Storefront Intelligence", "Inbound Supply Chain", "Outbound Logistics"]
    )

    insights = [
        # STOREFRONT
        {
            "id": "INS-S1",
            "pillar": "Storefront Intelligence",
            "title": "Severe Shopping Bag Abandonment Across Digital Sessions",
            "metric": "Cart Abandonment Rate = 93.25%",
            "metric_detail": "622 abandoned sessions out of 667 sessions with add-to-cart events.",
            "provenance": "synthetic",
            "root_cause": "Late display of shipping fees, mandatory account creation, or friction at payment transition.",
            "impact": "Suppresses return on ad spend (ROAS) and leads to heavy commercial leakage of high-intent shoppers.",
            "solution": "1-Click Express Checkout & Digital Wallets (Pix, Apple Pay, Google Pay) with upfront shipping preview.",
            "kpi": "Reduce Cart Abandonment Rate from 93.2% to < 75.0%; Increase checkout completion to >= 25.0%.",
            "prd": "PRD-02: 1-Click Express Checkout & Digital Wallets",
        },
        {
            "id": "INS-S2",
            "pillar": "Storefront Intelligence",
            "title": "Friction at Final Payment Gateway Authorization Step",
            "metric": "Checkout-to-Payment Drop-Off = 89.02%",
            "metric_detail": "Cumulative conversion collapses from 26.54% at checkout start to 2.91% at payment confirmation.",
            "provenance": "synthetic",
            "root_cause": "3D-Secure mobile redirects, lengthy 14-field forms, and lack of biometric 1-tap mobile payment.",
            "impact": "Direct lost revenue at the most expensive, lowest-funnel stage where acquisition costs have already been spent.",
            "solution": "Single-page responsive accordion checkout and 1-tap native mobile wallets.",
            "kpi": "Increase Checkout Completion Rate from 10.98% to >= 25.0%.",
            "prd": "PRD-02: 1-Click Express Checkout & Digital Wallets",
        },
        {
            "id": "INS-S3",
            "pillar": "Storefront Intelligence",
            "title": "Search Query Inefficiency with 86% Zero-Result Failure",
            "metric": "Zero-Result Search Rate = 85.96%",
            "metric_detail": "147 of 171 search queries returned zero matching products; Search CTR depressed at 14.04%.",
            "provenance": "synthetic",
            "root_cause": "Strict exact-string substring matching without fashion synonym dictionaries (e.g. sneakers vs shoes).",
            "impact": "Immediate customer bounce, high exit rates upon search execution, and inability to capture organic trend queries.",
            "solution": "Semantic Search Engine with fashion synonym dictionary and automated zero-result fallback merchandising.",
            "kpi": "Reduce Zero-Result Search Rate to < 15.0%; Lift Search CTR from 14.0% to >= 35.0%.",
            "prd": "PRD-03: Semantic Search & Dynamic Synonym Expansion",
        },
        {
            "id": "INS-S4",
            "pillar": "Storefront Intelligence",
            "title": "High Repeat Purchase Concentration with Dormant Customer Leakage",
            "metric": "Repeat Purchase Rate = 61.11%",
            "metric_detail": "11 of 18 unique buyers repeat, but 16.7% of customer base sits dormant with recency > 180 days.",
            "provenance": "observed",
            "root_cause": "Absence of automated post-purchase re-engagement workflows and category replenishment reminders.",
            "impact": "Over-reliance on costly paid acquisition rather than leveraging high-margin repeat customer LTV.",
            "solution": "Automated 30-day post-purchase replenishment recommendations and VIP loyalty rewards for Champions.",
            "kpi": "Dormant Customer Reactivation Rate >= 12.0%; 30-Day Repeat Rate >= 30.0%.",
            "prd": "OPT-08: Automated Post-Purchase Re-Engagement Engine",
        },
        # INBOUND
        {
            "id": "INS-I1",
            "pillar": "Inbound Supply Chain",
            "title": "Catalog Completeness Deficits in Season & Usage Attributes",
            "metric": "Catalog Completeness = 97.20%",
            "metric_detail": "10% of active SKUs missing season and 10% missing usage attributes.",
            "provenance": "reconciled",
            "root_cause": "Unenforced vendor onboarding upload forms lacking mandatory attribute validation rules.",
            "impact": "Products fail to appear in seasonal collections (e.g. Summer Essentials) or use-case filters (Sports/Casual).",
            "solution": "Automated Catalog Ingestion Schema Validator gating batch uploads.",
            "kpi": "Attain 100.0% attribute completeness across all active merchandise listings.",
            "prd": "OPT-06: Automated Catalog Ingestion Schema Validator",
        },
        {
            "id": "INS-I2",
            "pillar": "Inbound Supply Chain",
            "title": "Imminent Stockout Risk on Core Revenue-Driving SKU 1101",
            "metric": "Days of Cover (DoC) = 4.2 Days",
            "metric_detail": "Current stockout rate is 0.83% across SKU-days, but SKU 1101 requires urgent reorder of 340 units.",
            "provenance": "synthetic",
            "root_cause": "Static reorder thresholds that fail to dynamically scale with promotional demand surges.",
            "impact": "Lost revenue on top-selling hero styles and forced customer substitution to competing retailers.",
            "solution": "Dynamic Days of Cover Replenishment Alerts triggering automated purchase orders when DoC <= 14 days.",
            "kpi": "Maintain >= 99.8% in-stock availability on high-velocity core fashion SKUs.",
            "prd": "OPT-04: Dynamic Days of Cover Replenishment Alerts",
        },
        {
            "id": "INS-I3",
            "pillar": "Inbound Supply Chain",
            "title": "Working Capital Overhang in Stagnant Inventory (> 60 DoC)",
            "metric": "Average Days of Cover = 25.9 Days",
            "metric_detail": "Slow-moving tail styles exceed 60+ days of cover with minimal daily unit velocity.",
            "provenance": "synthetic",
            "root_cause": "Over-optimistic initial buys and off-season merchandise retention without structured markdown cadences.",
            "impact": "Trapped working capital, warehouse space congestion, and risk of terminal liquidation write-offs.",
            "solution": "Algorithmic Clearance Markdown Rules: auto-enroll items with DoC > 60 into tiered clearance discounts.",
            "kpi": "Increase inventory turnover from 3.5x to >= 5.5x; reduce overstocked SKUs by 50%.",
            "prd": "OPT-07: Algorithmic Clearance Markdown Rules",
        },
        {
            "id": "INS-I4",
            "pillar": "Inbound Supply Chain",
            "title": "Addiction to Flash Sales Compressing Gross Promotional Margins",
            "metric": "Average Discount Depth = 26.5%",
            "metric_detail": "43.3% of promotional campaigns are Flash Sales averaging 30.0% markdown depth.",
            "provenance": "synthetic",
            "root_cause": "Merchant reliance on short-term cash liquidation rather than full-price merchandising.",
            "impact": "Customer price anchoring (waiting for 30% off) and severe gross product margin compression.",
            "solution": "Enforce minimum gross margin floors (>= 40%) before promotional campaign activation.",
            "kpi": "Maintain blended promotional gross margin >= 48.0%; cap flash promotions at 24 hours.",
            "prd": "Pricing & Promotional Governance Protocol",
        },
        # OUTBOUND
        {
            "id": "INS-O1",
            "pillar": "Outbound Logistics",
            "title": "Carrier Transit Represents 75% of Total Fulfillment Lead Time",
            "metric": "Carrier Transit Share = 75.15%",
            "metric_detail": "Carrier in-transit duration averages 171.2 hours (7.1 days) vs. 56.7 hours for merchant dispatch.",
            "provenance": "observed",
            "root_cause": "Reliance on single ground postal carriers without regional line-haul hubs or dynamic route allocation.",
            "impact": "Long delivery transit drives customer cancellation risk, post-purchase anxiety, and negative NPS.",
            "solution": "Dynamic Multi-Carrier Routing Engine: dynamically route packages to the fastest performing regional carrier.",
            "kpi": "Reduce average transit duration from 7.1 days to <= 3.5 days; achieve OTD% >= 92.0%.",
            "prd": "OPT-05: Dynamic Multi-Carrier Routing Engine",
        },
        {
            "id": "INS-O2",
            "pillar": "Outbound Logistics",
            "title": "Substandard On-Time Delivery Rate Breaching Checkout Promises",
            "metric": "On-Time Delivery Rate (OTD%) = 69.70%",
            "metric_detail": "30.30% of customer orders arrive past the estimated delivery promise date; average delivery is 9.5 days.",
            "provenance": "observed",
            "root_cause": "Static, uncalibrated estimated delivery date (EDD) formulas ignoring regional distance variations.",
            "impact": "Elevates WISMO support tickets by 45% and drives pre-delivery order cancellations.",
            "solution": "Machine-learning dynamic EDD prediction engine with proactive transit delay notifications.",
            "kpi": "Increase On-Time Delivery Rate to >= 92.0%; reduce WISMO customer tickets by 50%.",
            "prd": "OPT-05: Outbound Carrier Intelligence & Dynamic EDD",
        },
        {
            "id": "INS-O3",
            "pillar": "Outbound Logistics",
            "title": "Excessive Reverse Logistics Costs Driven by Size & Fit Mismatch",
            "metric": "Apparel Item Return Rate = 23.21%",
            "metric_detail": "Size & Fit causes 38.46% of returns ($349.39 refund exposure); Activewear reaches a 60% return rate.",
            "provenance": "reconciled",
            "root_cause": "Inconsistent garment cuts across manufacturers and absence of interactive biometric size guidance.",
            "impact": "Double freight shipping expenses, restocking depreciation, and customer disappointment.",
            "solution": "Digital Fit & Sizing Intelligence Engine with interactive PDP 'Find Your Size' modal widget.",
            "kpi": "Reduce apparel item return rate to <= 15.0%; lower Size/Fit share of returns to < 20.0%.",
            "prd": "PRD-01: Digital Fit & Sizing Intelligence Engine",
        },
    ]

    filtered_insights = insights
    if pillar_filter != "All Pillars":
        filtered_insights = [i for i in insights if i["pillar"] == pillar_filter]

    st.markdown(f"**Displaying {len(filtered_insights)} Strategic Insights**")

    for idx, ins in enumerate(filtered_insights, start=1):
        with st.expander(f"{ins['id']}: {ins['title']} ({ins['pillar']})", expanded=(idx <= 3)):
            col_a, col_b = st.columns([4, 6])
            with col_a:
                render_metric_card(
                    label="Supporting Metric",
                    value=ins["metric"].split("=")[1].strip(),
                    sub_text=ins["metric"].split("=")[0].strip(),
                    provenance=ins["provenance"],
                )
                st.caption(f"**Telemetry Detail**: {ins['metric_detail']}")
            with col_b:
                st.markdown(f"**Root-Cause Hypothesis**: {ins['root_cause']}")
                st.markdown(f"**Business Impact**: {ins['impact']}")
                st.markdown(f"**Recommended Intervention**: {ins['solution']}")
                st.markdown(f"**Target Success KPI**: `{ins['kpi']}`")
                st.info(f"**Governing PRD / Backlog Item**: {ins['prd']}")
