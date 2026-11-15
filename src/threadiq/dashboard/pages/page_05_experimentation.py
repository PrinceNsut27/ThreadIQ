"""Page 5: A/B Experimentation & Decision Intelligence Dashboard."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.threadiq.dashboard.theme import (
    COLOR_PALETTE,
    PRIMARY_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    get_plotly_layout,
    render_metric_card,
)
from src.threadiq.experimentation.calculator import (
    calculate_sample_size_proportions,
    two_proportion_z_test,
)
from src.threadiq.experimentation.simulation import ExperimentSimulator


def render(engine):
    """Render A/B Experimentation & Statistical Testing Page."""
    st.markdown("""
    <div class="threadiq-header">
        <h1>A/B Experimentation & Decision Intelligence</h1>
        <p>Hypothesis testing, statistical power calculations, sample ratio mismatch (SRM) detection, and decision rules.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="callout-box">
        <strong>SIMULATION & METHODOLOGY NOTICE:</strong><br>
        The trials displayed below demonstrate ThreadIQ's statistical decision-making framework using simulated cohorts 
        (tagged <code>source_type = 'simulated_experiment'</code>). They represent mathematical power analysis, 
        confidence intervals, and SRM verification, and are not claimed as production causal proof prior to live deployment.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "Benchmark Experiments", "Interactive Sample Size Calculator", "Custom Hypothesis Tester"
    ])

    # ---------------------------------------------------------
    # TAB 1: BENCHMARK EXPERIMENTS
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Benchmark Product Opportunity Experiments")
        sim = ExperimentSimulator(random_seed=42)
        benchmarks = sim.run_benchmark_experiments()

        exp_selection = st.selectbox(
            "Select Experiment to Inspect:",
            list(benchmarks.keys()),
            format_func=lambda k: f"{k} — {benchmarks[k].experiment_name.split(':')[1].strip()}"
        )

        selected_res = benchmarks[exp_selection]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card(
                label="Control Rate",
                value=f"{selected_res.control_rate * 100:.2f}%",
                sub_text=f"{selected_res.control_conversions} / {selected_res.control_count}",
                provenance="synthetic",
            )
        with col2:
            render_metric_card(
                label="Treatment Rate",
                value=f"{selected_res.treatment_rate * 100:.2f}%",
                sub_text=f"{selected_res.treatment_conversions} / {selected_res.treatment_count}",
                provenance="synthetic",
            )
        with col3:
            render_metric_card(
                label="Relative Lift",
                value=f"{selected_res.relative_lift_percent:+.2f}%",
                sub_text=f"Absolute: {selected_res.absolute_lift * 100:+.2f} pts",
                provenance="synthetic",
            )
        with col4:
            render_metric_card(
                label="Statistical Outcome",
                value="SIGNIFICANT" if selected_res.is_statistically_significant else "INCONCLUSIVE",
                sub_text=f"p = {selected_res.p_value:.4e}",
                provenance="synthetic",
            )

        st.markdown("##### Detailed Statistical Verification")
        stat_data = {
            "Parameter": [
                "Evaluated Primary Metric",
                "Control Sample Size (nA)",
                "Treatment Sample Size (nB)",
                "Z-Statistic",
                "P-Value",
                "95% Confidence Interval",
                "Sample Ratio Mismatch (SRM)",
                "SRM Chi-Square P-Value",
                "Decision Recommendation",
            ],
            "Value": [
                selected_res.metric_name,
                f"{selected_res.control_count:,}",
                f"{selected_res.treatment_count:,}",
                f"{selected_res.z_statistic:.4f}",
                f"{selected_res.p_value:.6e}",
                f"[{selected_res.ci_lower * 100:.2f}%, {selected_res.ci_upper * 100:.2f}%]",
                "PASSED (No Mismatch)" if not selected_res.sample_ratio_mismatch_detected else "FAILED (SRM Detected)",
                f"{selected_res.srm_p_value:.4f}",
                "SHIP FEATURE (100% Rollout)" if selected_res.is_statistically_significant else "HOLD / RE-ITERATE",
            ]
        }
        st.dataframe(pd.DataFrame(stat_data), use_container_width=True, hide_index=True)

        # Plotly bar chart comparing Control vs Treatment
        fig_exp = go.Figure()
        fig_exp.add_trace(go.Bar(
            name="Control (A)",
            x=["Baseline"],
            y=[selected_res.control_rate * 100],
            marker_color="#64748B",
            text=[f"{selected_res.control_rate * 100:.2f}%"],
            textposition="outside",
        ))
        fig_exp.add_trace(go.Bar(
            name="Treatment (B)",
            x=["Baseline"],
            y=[selected_res.treatment_rate * 100],
            marker_color=PRIMARY_COLOR,
            text=[f"{selected_res.treatment_rate * 100:.2f}%"],
            textposition="outside",
        ))
        layout = get_plotly_layout(
            title=f"Variant Comparison: {selected_res.metric_name} (%)", height=320
        )
        fig_exp.update_layout(**layout, barmode="group", yaxis_title="Rate (%)")
        st.plotly_chart(fig_exp, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: INTERACTIVE SAMPLE SIZE CALCULATOR
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Statistical Power & Sample Size Calculator")
        st.markdown(
            "Plan your A/B test parameters to ensure statistical validity and prevent premature stopping."
        )

        c1, c2 = st.columns(2)
        with c1:
            baseline_pct = st.slider(
                "Baseline Conversion Rate (%)", min_value=0.5, max_value=50.0, value=10.0, step=0.5
            )
            rel_mde_pct = st.slider(
                "Minimum Detectable Effect / MDE (%)", min_value=1.0, max_value=100.0, value=20.0, step=1.0
            )
            daily_traffic = st.number_input(
                "Estimated Daily Eligible Visitors", min_value=100, max_value=500000, value=2500, step=100
            )
        with c2:
            alpha = st.selectbox(
                "Significance Level (Alpha)", [0.05, 0.01, 0.10], index=0,
                format_func=lambda x: f"{x} ({(1-x)*100:.0f}% Confidence)"
            )
            power = st.selectbox(
                "Statistical Power (1 - Beta)", [0.80, 0.90, 0.95], index=0,
                format_func=lambda x: f"{x*100:.0f}% Power"
            )

        analysis = calculate_sample_size_proportions(
            baseline_conversion=baseline_pct / 100.0,
            relative_mde=rel_mde_pct / 100.0,
            alpha=alpha,
            power=power,
            daily_traffic=daily_traffic,
        )

        st.markdown("##### Required Sample Size Specifications")
        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            render_metric_card(
                label="Sample Size Per Variant",
                value=f"{analysis.required_sample_size_per_variant:,}",
                sub_text=f"Total: {analysis.total_required_sample_size:,} visitors",
                provenance="reconciled",
            )
        with scol2:
            render_metric_card(
                label="Expected Target Rate",
                value=f"{analysis.expected_treatment_rate * 100:.2f}%",
                sub_text=f"Absolute Delta: {analysis.absolute_mde * 100:.2f} pts",
                provenance="reconciled",
            )
        with scol3:
            render_metric_card(
                label="Estimated Runtime",
                value=f"{analysis.estimated_days_to_complete:.1f} Days",
                sub_text=f"At {daily_traffic:,} visitors/day",
                provenance="reconciled",
            )

    # ---------------------------------------------------------
    # TAB 3: CUSTOM HYPOTHESIS TESTER
    # ---------------------------------------------------------
    with tab3:
        st.subheader("Custom Two-Proportion Hypothesis Tester")
        st.markdown("Enter trial observations to compute p-values, z-scores, and SRM checks.")

        hc1, hc2 = st.columns(2)
        with hc1:
            st.markdown("###### Control Group (A)")
            c_conv = st.number_input("Control Conversions", min_value=0, max_value=1000000, value=250)
            c_tot = st.number_input("Control Total Visitors", min_value=1, max_value=1000000, value=2500)
        with hc2:
            st.markdown("###### Treatment Group (B)")
            t_conv = st.number_input("Treatment Conversions", min_value=0, max_value=1000000, value=320)
            t_tot = st.number_input("Treatment Total Visitors", min_value=1, max_value=1000000, value=2500)

        if st.button("Evaluate Hypothesis Test", type="primary"):
            try:
                custom_res = two_proportion_z_test(
                    control_conversions=c_conv,
                    control_count=c_tot,
                    treatment_conversions=t_conv,
                    treatment_count=t_tot,
                    experiment_name="Custom Trial",
                )
                if custom_res.is_statistically_significant:
                    st.success(
                        f"STATISTICALLY SIGNIFICANT LIFT! Relative Lift: {custom_res.relative_lift_percent:+.2f}%, "
                        f"p = {custom_res.p_value:.6f}, 95% CI: [{custom_res.ci_lower*100:.2f}%, {custom_res.ci_upper*100:.2f}%]"
                    )
                else:
                    st.warning(
                        f"INCONCLUSIVE (p = {custom_res.p_value:.4f} >= 0.05). "
                        f"Difference in conversion is not statistically significant."
                    )
            except Exception as e:
                st.error(f"Error evaluating test: {e}")
