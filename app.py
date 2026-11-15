"""ThreadIQ — Fashion Commerce Product Intelligence & Operations Platform.

Main Streamlit Application Entrypoint.
"""

import sys
from pathlib import Path

# Ensure src/ is on python search path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st

from src.threadiq.dashboard.pages import (
    page_01_executive_overview,
    page_02_storefront,
    page_03_inbound,
    page_04_outbound,
    page_05_experimentation,
    page_06_roadmap,
    page_07_insights,
)
from src.threadiq.dashboard.theme import apply_custom_css
from sqlalchemy import inspect, text

from src.threadiq.data.loaders import create_database_schema, get_db_engine
from src.threadiq.data.pipeline import run_pipeline


# Streamlit Page Configuration
st.set_page_config(
    page_title="ThreadIQ — Fashion Product Intelligence",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global styling
apply_custom_css()


@st.cache_resource
def load_database():
    """Obtain a ready-to-query database, bootstrapping demo data on fresh deployments."""
    engine = get_db_engine()
    create_database_schema(engine)

    required_tables = {"fct_orders", "fct_order_payments", "dim_customers"}
    existing_tables = set(inspect(engine).get_table_names())

    # SQLite files are excluded from Git, so a fresh Streamlit deployment
    # needs to initialize its database before the dashboard executes queries.
    if not required_tables.issubset(existing_tables):
        st.info("First-time setup: building the ThreadIQ demo database. This may take a moment.")
        run_pipeline(database_url=str(engine.url), mock_if_missing=True)
    else:
        with engine.connect() as conn:
            order_count = conn.execute(text("SELECT COUNT(*) FROM fct_orders")).scalar_one()
        if order_count == 0:
            st.info("Initializing the empty ThreadIQ demo database.")
            run_pipeline(database_url=str(engine.url), mock_if_missing=True)

    final_tables = set(inspect(engine).get_table_names())
    missing = sorted(required_tables - final_tables)
    if missing:
        raise RuntimeError(
            "ThreadIQ database initialization did not create required tables: "
            + ", ".join(missing)
        )
    return engine


def main():
    """Main application navigation and router."""
    engine = load_database()

    # Sidebar Brand & Navigation
    with st.sidebar:
        st.markdown("""
        <div style="padding: 1rem 0; text-align: center;">
            <h2 style="margin: 0; color: #1E293B; font-weight: 800;">🧵 ThreadIQ</h2>
            <p style="margin: 0; color: #64748B; font-size: 0.85rem;">Product Intelligence & Operations</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Platform Modules")

        page_selection = st.radio(
            "Select Dashboard View:",
            [
                "Executive Overview",
                "Storefront Intelligence",
                "Inbound Intelligence",
                "Outbound Intelligence",
                "A/B Experimentation",
                "Product Roadmap & RICE",
                "Strategic Insights & PRDs",
            ],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.subheader("Data Provenance")
        st.markdown("""
        - <span class="badge-observed">OBSERVED</span> Real Olist transactions & orders
        - <span class="badge-synthetic">SYNTHETIC</span> Realistic clickstream & inventory
        - <span class="badge-reconciled">RECONCILED</span> Multi-source calculated metrics
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.caption("ThreadIQ v1.0.0-production | Python 3.13 | SQLite")

    # Page Dispatcher
    if page_selection == "Executive Overview":
        page_01_executive_overview.render(engine)
    elif page_selection == "Storefront Intelligence":
        page_02_storefront.render(engine)
    elif page_selection == "Inbound Intelligence":
        page_03_inbound.render(engine)
    elif page_selection == "Outbound Intelligence":
        page_04_outbound.render(engine)
    elif page_selection == "A/B Experimentation":
        page_05_experimentation.render(engine)
    elif page_selection == "Product Roadmap & RICE":
        page_06_roadmap.render(engine)
    elif page_selection == "Strategic Insights & PRDs":
        page_07_insights.render(engine)


if __name__ == "__main__":
    main()
