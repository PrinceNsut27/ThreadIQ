"""Unit and integration tests for ThreadIQ Experimentation & Decision Intelligence."""

import numpy as np
import pytest

from src.threadiq.experimentation.calculator import (
    calculate_minimum_detectable_effect,
    calculate_sample_size_continuous,
    calculate_sample_size_proportions,
    check_sample_ratio_mismatch,
    difference_in_means_test,
    two_proportion_z_test,
)
from src.threadiq.experimentation.prioritization import (
    PrioritizationTier,
    RICEOpportunity,
    RICEPrioritizer,
)
from src.threadiq.experimentation.simulation import (
    ExperimentSimulator,
)


# ---------------------------------------------------------------------------
# 1. SAMPLE SIZE & POWER CALCULATOR TESTS
# ---------------------------------------------------------------------------

def test_sample_size_proportions_basic():
    """Test sample size calculation for proportions with standard parameters."""
    analysis = calculate_sample_size_proportions(
        baseline_conversion=0.10,
        relative_mde=0.20,  # 20% relative lift -> target 0.12
        alpha=0.05,
        power=0.80,
    )
    assert analysis.required_sample_size_per_variant > 0
    assert analysis.total_required_sample_size == analysis.required_sample_size_per_variant * 2
    assert analysis.relative_mde_percent == 20.0
    assert analysis.expected_treatment_rate == 0.12
    # For p=0.10, MDE=20%, required sample size is typically ~3,800 to ~4,000 per variant
    assert 3000 <= analysis.required_sample_size_per_variant <= 5000


def test_sample_size_proportions_invalid_inputs():
    """Test error handling for invalid baseline or MDE values."""
    with pytest.raises(ValueError):
        calculate_sample_size_proportions(baseline_conversion=1.5, relative_mde=0.1)
    with pytest.raises(ValueError):
        calculate_sample_size_proportions(baseline_conversion=0.05, relative_mde=0.0)
    with pytest.raises(ValueError):
        calculate_sample_size_proportions(baseline_conversion=0.05, relative_mde=0.1, alpha=1.2)


def test_sample_size_continuous():
    """Test sample size calculation for continuous metrics (AOV)."""
    analysis = calculate_sample_size_continuous(
        std_dev=30.0,
        absolute_mde=5.0,
        alpha=0.05,
        power=0.80,
        daily_traffic=100,
    )
    assert analysis.required_sample_size_per_variant > 0
    assert analysis.estimated_days_to_complete is not None
    assert analysis.estimated_days_to_complete > 0


def test_minimum_detectable_effect():
    """Test MDE estimation given fixed sample size."""
    mde = calculate_minimum_detectable_effect(
        sample_size_per_variant=5000,
        baseline_conversion=0.05,
    )
    assert mde > 0.0
    assert isinstance(mde, float)


# ---------------------------------------------------------------------------
# 2. STATISTICAL HYPOTHESIS TESTING
# ---------------------------------------------------------------------------

def test_two_proportion_z_test_significant():
    """Test detection of statistically significant conversion difference."""
    res = two_proportion_z_test(
        control_conversions=100,
        control_count=1000,  # 10.0%
        treatment_conversions=150,
        treatment_count=1000,  # 15.0%
        alpha=0.05,
        experiment_name="Express Checkout Test",
    )
    assert res.is_statistically_significant is True
    assert res.p_value < 0.05
    assert res.relative_lift_percent == 50.0
    assert res.absolute_lift == 0.05
    assert res.ci_lower > 0.0
    assert res.provenance == "simulated_experiment"


def test_two_proportion_z_test_non_significant():
    """Test that minor variance is not falsely flagged as significant."""
    res = two_proportion_z_test(
        control_conversions=100,
        control_count=1000,
        treatment_conversions=102,
        treatment_count=1000,
        alpha=0.05,
    )
    assert res.is_statistically_significant is False
    assert res.p_value > 0.05
    assert res.ci_lower < 0.0 < res.ci_upper


def test_sample_ratio_mismatch_detection():
    """Test detection of Sample Ratio Mismatch (SRM)."""
    # Healthy 50/50 split
    srm_healthy, p_healthy = check_sample_ratio_mismatch(5000, 4980)
    assert srm_healthy is False
    assert p_healthy > 0.001

    # Severely broken split (6000 vs 4000 instead of 50/50)
    srm_broken, p_broken = check_sample_ratio_mismatch(6000, 4000)
    assert srm_broken is True
    assert p_broken < 0.0001


def test_difference_in_means_welch():
    """Test Welch's t-test for continuous order values."""
    np.random.seed(42)
    ctrl = np.random.normal(loc=150.0, scale=20.0, size=500)
    trt = np.random.normal(loc=170.0, scale=20.0, size=500)

    res = difference_in_means_test(ctrl, trt, alpha=0.05, metric_name="AOV")
    assert res.is_statistically_significant is True
    assert res.p_value < 0.001
    assert res.absolute_lift > 15.0


# ---------------------------------------------------------------------------
# 3. RICE PRIORITISATION TESTS
# ---------------------------------------------------------------------------

def test_rice_opportunity_score_calculation():
    """Test RICE formula: (Reach * Impact * Confidence) / Effort."""
    opp = RICEOpportunity(
        opportunity_id="OPT-01",
        area="Storefront",
        problem_statement="High checkout drop-off",
        proposed_feature="1-Click Express Checkout",
        reach=10000,
        impact=3.0,
        confidence=0.8,
        effort=2.0,
        rationale="Fixes 89% payment drop-off",
    )
    # Score = (10000 * 3.0 * 0.8) / 2.0 = 24000 / 2.0 = 12000.0
    assert opp.rice_score == 12000.0


def test_rice_prioritizer_ranking_and_tiering():
    """Test that prioritizer ranks descending and assigns Now/Next/Later tiers."""
    prioritizer = RICEPrioritizer()

    opp1 = RICEOpportunity(
        opportunity_id="OPT-LOW",
        area="Inbound",
        problem_statement="Minor catalog styling tag",
        proposed_feature="Tagging UI",
        reach=500,
        impact=0.5,
        confidence=0.5,
        effort=3.0,
        rationale="Low impact",
    )
    opp2 = RICEOpportunity(
        opportunity_id="OPT-HIGH",
        area="Outbound",
        problem_statement="High fit return rate",
        proposed_feature="Fit Advisor Widget",
        reach=25000,
        impact=3.0,
        confidence=0.9,
        effort=2.5,
        rationale="Massive return savings",
    )
    opp3 = RICEOpportunity(
        opportunity_id="OPT-MED",
        area="Storefront",
        problem_statement="Search zero results",
        proposed_feature="Synonym Expansion",
        reach=8000,
        impact=2.0,
        confidence=0.8,
        effort=1.5,
        rationale="Medium impact discovery",
    )

    prioritizer.add_opportunity(opp1)
    prioritizer.add_opportunity(opp2)
    prioritizer.add_opportunity(opp3)

    ranked = prioritizer.rank()
    assert len(ranked) == 3
    assert ranked[0].opportunity_id == "OPT-HIGH"
    assert ranked[1].opportunity_id == "OPT-MED"
    assert ranked[2].opportunity_id == "OPT-LOW"

    df_ranked = prioritizer.to_dataframe()
    assert not df_ranked.empty
    assert "RICE Score" in df_ranked.columns
    assert "Tier" in df_ranked.columns


# ---------------------------------------------------------------------------
# 4. EXPERIMENT SIMULATOR TESTS
# ---------------------------------------------------------------------------

def test_experiment_simulator_runs():
    """Test simulation engine generates tagged cohorts and statistical analysis."""
    sim = ExperimentSimulator(random_seed=42)
    cohort = sim.simulate_proportion_experiment(
        experiment_name="Simulated Test",
        metric_name="Conversion Rate",
        n_control=1000,
        n_treatment=1000,
        baseline_rate=0.10,
        relative_lift=0.30,
    )
    assert cohort.source_type == "simulated_experiment"
    assert len(cohort.control_data) == 1000
    assert len(cohort.treatment_data) == 1000
    assert cohort.result.provenance == "simulated_experiment"


def test_benchmark_experiments_execution():
    """Test execution of the 3 benchmark fashion experiments."""
    sim = ExperimentSimulator(random_seed=42)
    benchmarks = sim.run_benchmark_experiments()

    assert "EXP-01" in benchmarks
    assert "EXP-02" in benchmarks
    assert "EXP-03" in benchmarks

    for exp_id, res in benchmarks.items():
        assert res.provenance == "simulated_experiment"
        assert res.control_count > 0
        assert res.treatment_count > 0
        assert 0.0 <= res.p_value <= 1.0
