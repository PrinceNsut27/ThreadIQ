"""Dashboard theming, custom styling, Plotly layout templates, and UI components."""

import plotly.graph_objects as go
import streamlit as st

PRIMARY_COLOR = "#2563EB"     # Royal Blue
SECONDARY_COLOR = "#7C3AED"   # Deep Purple
SUCCESS_COLOR = "#059669"     # Emerald Green
WARNING_COLOR = "#D97706"     # Amber
DANGER_COLOR = "#DC2626"      # Coral Red
NEUTRAL_DARK = "#0F172A"      # Slate 900
NEUTRAL_LIGHT = "#F8FAFC"     # Slate 50
BORDER_COLOR = "#E2E8F0"      # Slate 200

COLOR_PALETTE = [
    "#2563EB", "#7C3AED", "#059669", "#D97706",
    "#DC2626", "#0284C7", "#4F46E5", "#0D9488"
]


def apply_custom_css():
    """Inject custom responsive CSS into the Streamlit app."""
    css = """
    <style>
    /* Global layout adjustments */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }
    
    /* Header card */
    .threadiq-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .threadiq-header h1 {
        color: #FFFFFF !important;
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
    }
    .threadiq-header p {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-top: 0.35rem;
        margin-bottom: 0;
    }

    /* Metric card */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0.1rem 0;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #64748B;
    }
    
    /* Provenance pill badges */
    .badge-observed {
        display: inline-block;
        background-color: #DBEAFE;
        color: #1E40AF;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 9999px;
        text-transform: uppercase;
    }
    .badge-synthetic {
        display: inline-block;
        background-color: #FEF3C7;
        color: #92400E;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 9999px;
        text-transform: uppercase;
    }
    .badge-reconciled {
        display: inline-block;
        background-color: #E0E7FF;
        color: #3730A3;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: 9999px;
        text-transform: uppercase;
    }
    
    /* Callout notice boxes */
    .callout-box {
        background-color: #F8FAFC;
        border-left: 4px solid #2563EB;
        padding: 1rem 1.25rem;
        border-radius: 4px;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #334155;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def get_plotly_layout(title: str = "", height: int = 400) -> dict:
    """Return standard clean Plotly layout configuration."""
    return {
        "title": {
            "text": title,
            "font": {"size": 14, "color": NEUTRAL_DARK, "family": "Inter, sans-serif"},
            "x": 0.02,
        },
        "height": height,
        "margin": {"l": 40, "r": 30, "t": 50, "b": 40},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "xaxis": {
            "gridcolor": "#F1F5F9",
            "zerolinecolor": "#E2E8F0",
            "tickfont": {"size": 11, "color": "#64748B"},
        },
        "yaxis": {
            "gridcolor": "#F1F5F9",
            "zerolinecolor": "#E2E8F0",
            "tickfont": {"size": 11, "color": "#64748B"},
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 11, "color": "#64748B"},
        },
    }


def render_metric_card(
    label: str,
    value: str,
    sub_text: str = "",
    provenance: str = "observed",
    delta_color: str = "normal",
):
    """Render a styled metric KPI card with data lineage badge."""
    badge_cls = "badge-observed"
    badge_label = "OBSERVED"
    if provenance == "synthetic":
        badge_cls = "badge-synthetic"
        badge_label = "SYNTHETIC"
    elif provenance == "reconciled":
        badge_cls = "badge-reconciled"
        badge_label = "RECONCILED"

    html = f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="metric-label">{label}</div>
            <span class="{badge_cls}">{badge_label}</span>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub_text}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
