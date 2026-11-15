"""Page 6: Product Roadmap & RICE Prioritization Dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.threadiq.dashboard.theme import (
    COLOR_PALETTE,
    PRIMARY_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    get_plotly_layout,
    render_metric_card,
)
from src.threadiq.experimentation.prioritization import (
    PrioritizationTier,
    RICEOpportunity,
    RICEPrioritizer,
)


def _build_default_prioritizer() -> RICEPrioritizer:
    """Instantiate and populate the RICE prioritizer with ThreadIQ's analytical opportunities."""
    p = RICEPrioritizer()
    opportunities = [
        RICEOpportunity(
            opportunity_id="OPT-01",
            area="Outbound",
            problem_statement="23.2% apparel return rate; 38.5% driven by size & fit ($938 exposure)",
            proposed_feature="Digital Fit & Sizing Intelligence Engine",
            reach=25000,
            impact=3.0,
            confidence=0.90,
            effort=2.5,
            rationale="Eliminates primary reverse logistics driver; verified return telemetry.",
            priority_tier=PrioritizationTier.NOW,
        ),
        RICEOpportunity(
            opportunity_id="OPT-02",
            area="Storefront",
            problem_statement="89.0% checkout-to-payment drop-off; 93.3% cart abandonment",
            proposed_feature="1-Click Express Checkout & Digital Wallets",
            reach=20000,
            impact=3.0,
            confidence=0.85,
            effort=2.0,
            rationale="Unblocks highest-intent funnel stage; direct GMV lift.",
            priority_tier=PrioritizationTier.NOW,
        ),
        RICEOpportunity(
            opportunity_id="OPT-03",
            area="Storefront",
            problem_statement="86.0% zero-result search rate; 14.0% search CTR",
            proposed_feature="Semantic Search & Dynamic Synonym Expansion",
            reach=15000,
            impact=2.0,
            confidence=0.80,
            effort=1.5,
            rationale="Converts dead-end queries into active PDP views.",
            priority_tier=PrioritizationTier.NOW,
        ),
        RICEOpportunity(
            opportunity_id="OPT-04",
            area="Inbound",
            problem_statement="Core SKU 1101 at 4.2 Days of Cover (critical stockout risk)",
            proposed_feature="Dynamic Days of Cover Replenishment Alerts",
            reach=12000,
            impact=2.0,
            confidence=0.90,
            effort=1.5,
            rationale="Prevents stockouts on top revenue-driving fashion listings.",
            priority_tier=PrioritizationTier.NOW,
        ),
        RICEOpportunity(
            opportunity_id="OPT-05",
            area="Outbound",
            problem_statement="Carrier transit represents 75.2% of fulfillment; 30.3% late deliveries",
            proposed_feature="Dynamic Multi-Carrier Routing Engine",
            reach=18000,
            impact=2.0,
            confidence=0.80,
            effort=2.5,
            rationale="Routes destination postal codes to highest SLA carrier.",
            priority_tier=PrioritizationTier.NEXT,
        ),
        RICEOpportunity(
            opportunity_id="OPT-06",
            area="Inbound",
            problem_statement="10% of catalog SKUs missing season/usage attributes",
            proposed_feature="Automated Catalog Ingestion Schema Validator",
            reach=5000,
            impact=1.0,
            confidence=0.95,
            effort=0.5,
            rationale="Low effort, high data hygiene return on batch uploads.",
            priority_tier=PrioritizationTier.NEXT,
        ),
        RICEOpportunity(
            opportunity_id="OPT-07",
            area="Inbound",
            problem_statement="Slow-moving styles exceeding 60 Days of Cover",
            proposed_feature="Algorithmic Clearance Markdown Rules",
            reach=8000,
            impact=1.0,
            confidence=0.80,
            effort=1.0,
            rationale="Automated tiered discounting clears trapped working capital.",
            priority_tier=PrioritizationTier.NEXT,
        ),
        RICEOpportunity(
            opportunity_id="OPT-08",
            area="Storefront",
            problem_statement="16.7% dormant buyers post-initial order",
            proposed_feature="Automated Post-Purchase Re-Engagement Engine",
            reach=6000,
            impact=1.0,
            confidence=0.80,
            effort=1.0,
            rationale="Drives repeat customer LTV through automated styling tips.",
            priority_tier=PrioritizationTier.NEXT,
        ),
        RICEOpportunity(
            opportunity_id="OPT-09",
            area="Outbound",
            problem_statement="56.7 hour average merchant dispatch delay",
            proposed_feature="Merchant Fulfillment SLA Portal & Penalty Alerts",
            reach=4000,
            impact=1.0,
            confidence=0.80,
            effort=1.0,
            rationale="Enforces 48-hour merchant packing SLA.",
            priority_tier=PrioritizationTier.LATER,
        ),
        RICEOpportunity(
            opportunity_id="OPT-10",
            area="Storefront",
            problem_statement="High return rate in Eyewear (50%) and Activewear (60%)",
            proposed_feature="Augmented Reality Virtual Try-On (AR PDP)",
            reach=10000,
            impact=2.0,
            confidence=0.50,
            effort=4.0,
            rationale="High complexity; 3D asset modeling required.",
            priority_tier=PrioritizationTier.LATER,
        ),
    ]
    for o in opportunities:
        p.add_opportunity(o)
    return p


def render(engine):
    """Render Product Roadmap & RICE Prioritization Page."""
    st.markdown("""
    <div class="threadiq-header">
        <h1>Product Strategy, Backlog & Roadmap</h1>
        <p>RICE prioritized feature backlog, execution horizon (Now/Next/Later), and cross-functional dependency tracking.</p>
    </div>
    """, unsafe_allow_html=True)

    prioritizer = _build_default_prioritizer()
    df_ranked = prioritizer.to_dataframe()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            label="Total Backlog Initiatives",
            value=str(len(df_ranked)),
            sub_text="Scored via RICE methodology",
            provenance="reconciled",
        )
    with col2:
        render_metric_card(
            label="Tier 1 (NOW) Initiatives",
            value=str(len(df_ranked[df_ranked["Tier"] == "Now"])),
            sub_text="In active sprint cycle",
            provenance="reconciled",
        )
    with col3:
        render_metric_card(
            label="Tier 2 (NEXT) Initiatives",
            value=str(len(df_ranked[df_ranked["Tier"] == "Next"])),
            sub_text="Planned subsequent quarter",
            provenance="reconciled",
        )
    with col4:
        render_metric_card(
            label="Top RICE Score",
            value=f"{df_ranked.iloc[0]['RICE Score']:,.0f}",
            sub_text=f"ID: {df_ranked.iloc[0]['ID']} (Fit Advisor)",
            provenance="reconciled",
        )

    tab1, tab2, tab3 = st.tabs([
        "RICE Prioritized Backlog", "Roadmap Timeline", "Dependencies & Active Risks"
    ])

    # ---------------------------------------------------------
    # TAB 1: RICE BACKLOG
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Ranked Product Opportunity Backlog")

        fcol1, fcol2 = st.columns(2)
        with fcol1:
            tier_filter = st.selectbox(
                "Filter by Execution Tier:", ["All Tiers", "Now", "Next", "Later"]
            )
        with fcol2:
            area_filter = st.selectbox(
                "Filter by Product Area:", ["All Areas", "Storefront", "Inbound", "Outbound"]
            )

        filtered_df = df_ranked.copy()
        if tier_filter != "All Tiers":
            filtered_df = filtered_df[filtered_df["Tier"] == tier_filter]
        if area_filter != "All Areas":
            filtered_df = filtered_df[filtered_df["Area"] == area_filter]

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        # Plotly horizontal bar chart of RICE scores
        fig_rice = px.bar(
            df_ranked,
            x="RICE Score",
            y="Proposed Feature",
            orientation="h",
            color="Tier",
            color_discrete_map={"Now": "#2563EB", "Next": "#7C3AED", "Later": "#94A3B8"},
            title="RICE Score Comparison across Candidate Opportunities",
        )
        fig_rice.update_layout(**get_plotly_layout(height=420))
        st.plotly_chart(fig_rice, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: ROADMAP TIMELINE
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Implementation Roadmap & Quarterly Horizons")
        st.markdown("""
        *Note: All dates are planning estimates subject to experiment outcome gates.*
        """)

        gantt_records = [
            {"Task": "PRD-01: Fit & Sizing Intelligence", "Start": "2026-11-16", "End": "2026-12-15", "Tier": "Now", "Area": "Outbound"},
            {"Task": "PRD-02: 1-Click Express Checkout", "Start": "2026-11-20", "End": "2026-12-20", "Tier": "Now", "Area": "Storefront"},
            {"Task": "PRD-03: Semantic Search Expansion", "Start": "2026-11-16", "End": "2026-12-05", "Tier": "Now", "Area": "Storefront"},
            {"Task": "Dynamic DoC Replenishment Alerts", "Start": "2026-12-21", "End": "2027-01-20", "Tier": "Now", "Area": "Inbound"},
            {"Task": "Catalog Ingestion Validator", "Start": "2027-01-10", "End": "2027-02-01", "Tier": "Next", "Area": "Inbound"},
            {"Task": "Dynamic Multi-Carrier Routing", "Start": "2027-01-05", "End": "2027-02-15", "Tier": "Next", "Area": "Outbound"},
            {"Task": "Algorithmic Clearance Markdowns", "Start": "2027-02-16", "End": "2027-03-31", "Tier": "Next", "Area": "Inbound"},
            {"Task": "Merchant Fulfillment Portal", "Start": "2027-03-01", "End": "2027-04-15", "Tier": "Later", "Area": "Outbound"},
            {"Task": "AR Virtual Try-On Engine", "Start": "2027-04-01", "End": "2027-05-30", "Tier": "Later", "Area": "Storefront"},
        ]
        df_gantt = pd.DataFrame(gantt_records)
        df_gantt["Start"] = pd.to_datetime(df_gantt["Start"])
        df_gantt["End"] = pd.to_datetime(df_gantt["End"])

        fig_gantt = px.timeline(
            df_gantt,
            x_start="Start",
            x_end="End",
            y="Task",
            color="Tier",
            color_discrete_map={"Now": "#2563EB", "Next": "#7C3AED", "Later": "#94A3B8"},
            title="ThreadIQ Estimated Implementation Horizons (Q4 2026 - Q2 2027)",
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(**get_plotly_layout(height=380))
        st.plotly_chart(fig_gantt, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 3: DEPENDENCIES & RISKS
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Cross-Functional Dependencies & Active Risk Log")

        st.markdown("##### Critical Path Dependencies")
        dep_data = {
            "ID": ["DEP-01", "DEP-02", "DEP-03", "DEP-04"],
            "Dependent Feature": [
                "PRD-02: Express Checkout & Wallets",
                "PRD-01: Fit & Sizing Intelligence",
                "PRD-03: Semantic Search Expansion",
                "OPT-05: Multi-Carrier Routing",
            ],
            "Owner Team": ["External Gateway Partner", "Inbound Merchandising", "Taxonomy & Search", "3PL Carriers"],
            "Target Date": ["2026-11-20", "2026-11-25", "2026-11-18", "2026-12-15"],
            "Status": ["ON TRACK", "ON TRACK", "COMPLETED", "SCHEDULED"],
        }
        st.dataframe(pd.DataFrame(dep_data), use_container_width=True, hide_index=True)

        st.markdown("##### High-Impact Risk Log")
        risk_data = {
            "ID": ["RSK-01", "RSK-02", "RSK-03", "RSK-04"],
            "Area": ["Outbound", "Storefront", "Storefront", "Inbound"],
            "Description": [
                "Sizing model recommends wrong size due to supplier cut variance.",
                "Third-party payment gateway downtime halts checkout.",
                "Overly broad synonym expansion returns irrelevant items.",
                "Supplier batch uploads omit mandatory season/usage fields.",
            ],
            "Severity": ["High", "Critical", "Medium", "Medium"],
            "Mitigation Strategy": [
                "Ingest stretch elasticity & feedback loop calibration.",
                "Implement redundant secondary payment gateway fallback.",
                "Restrict expansion to verified dictionary pairs.",
                "Enforce automated schema validator on batch ingestion.",
            ],
            "Status": ["MITIGATING", "MONITORED", "CONTROLLED", "MITIGATED"],
        }
        st.dataframe(pd.DataFrame(risk_data), use_container_width=True, hide_index=True)
