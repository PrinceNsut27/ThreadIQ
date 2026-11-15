"""Tests for ThreadIQ Streamlit Dashboard structure, imports, and component integrity."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.threadiq.dashboard.pages import (
    page_01_executive_overview,
    page_02_storefront,
    page_03_inbound,
    page_04_outbound,
    page_05_experimentation,
    page_06_roadmap,
    page_07_insights,
)
from src.threadiq.dashboard.pages.page_06_roadmap import _build_default_prioritizer
from src.threadiq.dashboard.theme import (
    COLOR_PALETTE,
    PRIMARY_COLOR,
    get_plotly_layout,
)
from src.threadiq.data.loaders import get_db_engine


def test_dashboard_page_modules_import():
    """Verify all dashboard page modules import cleanly without runtime or syntax errors."""
    assert callable(page_01_executive_overview.render)
    assert callable(page_02_storefront.render)
    assert callable(page_03_inbound.render)
    assert callable(page_04_outbound.render)
    assert callable(page_05_experimentation.render)
    assert callable(page_06_roadmap.render)
    assert callable(page_07_insights.render)


def test_plotly_theme_layout():
    """Test Plotly layout helper configuration and theme parameters."""
    layout = get_plotly_layout(title="Test Chart", height=450)
    assert layout["title"]["text"] == "Test Chart"
    assert layout["height"] == 450
    assert "xaxis" in layout
    assert "yaxis" in layout
    assert PRIMARY_COLOR.startswith("#")
    assert len(COLOR_PALETTE) >= 5


def test_roadmap_prioritizer_default():
    """Verify default RICE prioritizer builds properly with ranked backlog."""
    prioritizer = _build_default_prioritizer()
    ranked = prioritizer.rank()
    assert len(ranked) == 10
    df = prioritizer.to_dataframe()
    assert not df.empty
    assert "RICE Score" in df.columns
    assert "Tier" in df.columns
    # Top initiative should be OPT-01
    assert df.iloc[0]["ID"] == "OPT-01"


def test_database_engine_connection_dashboard():
    """Verify that dashboard can acquire an active database connection."""
    engine = get_db_engine()
    with engine.connect() as conn:
        assert conn is not None


def test_apptest_all_seven_pages():
    """End-to-end integration test verifying that all 7 dashboard pages render without exceptions."""
    pages = [
        "Executive Overview",
        "Storefront Intelligence",
        "Inbound Intelligence",
        "Outbound Intelligence",
        "A/B Experimentation",
        "Product Roadmap & RICE",
        "Strategic Insights & PRDs",
    ]

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    for p in pages:
        at = AppTest.from_file(str(app_path), default_timeout=30)
        at.run()
        # Switch to the requested radio page
        at.radio[0].set_value(p).run()
        assert len(at.exception) == 0, f"Page '{p}' threw {len(at.exception)} unhandled exceptions: {at.exception}"
