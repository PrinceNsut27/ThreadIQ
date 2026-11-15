"""A/B experiment simulation module for ThreadIQ decision intelligence demonstration.

Generates statistically grounded synthetic experimental cohorts to demonstrate
hypothesis testing, power analysis, sample ratio mismatch checks, and decision gating.
ALL outputs are strictly tagged as 'simulated_experiment'.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.threadiq.experimentation.calculator import (
    ExperimentResult,
    difference_in_means_test,
    two_proportion_z_test,
)


@dataclass
class SimulatedCohort:
    """Detailed observation records for simulated experimental branches."""

    experiment_id: str
    control_data: pd.DataFrame
    treatment_data: pd.DataFrame
    result: ExperimentResult
    source_type: str = "simulated_experiment"


class ExperimentSimulator:
    """Simulator generating synthetic experimental trial data for product decision modeling."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)

    def simulate_proportion_experiment(
        self,
        experiment_name: str,
        metric_name: str,
        n_control: int,
        n_treatment: int,
        baseline_rate: float,
        relative_lift: float,
        alpha: float = 0.05,
    ) -> SimulatedCohort:
        """Simulate a binary conversion rate A/B test with Bernoulli trials.

        Args:
            experiment_name: Descriptive name of the experiment.
            metric_name: Name of evaluated primary KPI.
            n_control: Visitor count in Control branch.
            n_treatment: Visitor count in Treatment branch.
            baseline_rate: Ground truth conversion probability for Control.
            relative_lift: True underlying relative lift for Treatment (e.g. 0.20 for +20%).
            alpha: Significance level (default 0.05).

        Returns:
            SimulatedCohort containing raw observation DataFrames and statistical evaluation.
        """
        treatment_rate = max(0.0001, min(0.9999, baseline_rate * (1.0 + relative_lift)))

        # Generate Bernoulli outcomes
        ctrl_outcomes = self.rng.binomial(n=1, p=baseline_rate, size=n_control)
        trt_outcomes = self.rng.binomial(n=1, p=treatment_rate, size=n_treatment)

        df_ctrl = pd.DataFrame({
            "session_id": [f"sim_ctrl_{i:06d}" for i in range(n_control)],
            "variant": "Control (A)",
            "converted": ctrl_outcomes,
            "source_type": "simulated_experiment",
        })
        df_trt = pd.DataFrame({
            "session_id": [f"sim_trt_{i:06d}" for i in range(n_treatment)],
            "variant": "Treatment (B)",
            "converted": trt_outcomes,
            "source_type": "simulated_experiment",
        })

        result = two_proportion_z_test(
            control_conversions=int(np.sum(ctrl_outcomes)),
            control_count=n_control,
            treatment_conversions=int(np.sum(trt_outcomes)),
            treatment_count=n_treatment,
            alpha=alpha,
            experiment_name=experiment_name,
            metric_name=metric_name,
            provenance="simulated_experiment",
        )

        return SimulatedCohort(
            experiment_id=experiment_name,
            control_data=df_ctrl,
            treatment_data=df_trt,
            result=result,
            source_type="simulated_experiment",
        )

    def simulate_continuous_experiment(
        self,
        experiment_name: str,
        metric_name: str,
        n_control: int,
        n_treatment: int,
        mean_control: float,
        std_control: float,
        absolute_lift: float,
        alpha: float = 0.05,
    ) -> SimulatedCohort:
        """Simulate a continuous metric A/B test (e.g. Average Order Value) with log-normal distributions.

        Args:
            experiment_name: Experiment identifier.
            metric_name: Evaluated metric (e.g. Order Value).
            n_control: Sample size in Control.
            n_treatment: Sample size in Treatment.
            mean_control: Baseline mean.
            std_control: Baseline standard deviation.
            absolute_lift: True delta added to treatment mean.
            alpha: Significance level.

        Returns:
            SimulatedCohort with observations and Welch's t-test result.
        """
        # Truncate at zero for financial values
        ctrl_vals = np.maximum(0.0, self.rng.normal(loc=mean_control, scale=std_control, size=n_control))
        trt_vals = np.maximum(
            0.0,
            self.rng.normal(loc=mean_control + absolute_lift, scale=std_control, size=n_treatment),
        )

        df_ctrl = pd.DataFrame({
            "order_id": [f"sim_ord_ctrl_{i:05d}" for i in range(n_control)],
            "variant": "Control (A)",
            "order_value": np.round(ctrl_vals, 2),
            "source_type": "simulated_experiment",
        })
        df_trt = pd.DataFrame({
            "order_id": [f"sim_ord_trt_{i:05d}" for i in range(n_treatment)],
            "variant": "Treatment (B)",
            "order_value": np.round(trt_vals, 2),
            "source_type": "simulated_experiment",
        })

        result = difference_in_means_test(
            control_values=ctrl_vals,
            treatment_values=trt_vals,
            alpha=alpha,
            experiment_name=experiment_name,
            metric_name=metric_name,
            provenance="simulated_experiment",
        )

        return SimulatedCohort(
            experiment_id=experiment_name,
            control_data=df_ctrl,
            treatment_data=df_trt,
            result=result,
            source_type="simulated_experiment",
        )

    def run_benchmark_experiments(self) -> Dict[str, ExperimentResult]:
        """Execute the three benchmark product opportunity experiments in simulation mode.

        Returns dictionary of ExperimentResults:
        1. EXP-01: Fit & Sizing Intelligence Widget (Item Return Rate reduction)
        2. EXP-02: 1-Click Express Checkout & Digital Wallets (Checkout Completion Rate lift)
        3. EXP-03: Semantic Search & Synonym Expansion (Search CTR lift & Zero-Result reduction)
        """
        results = {}

        # 1. Fit & Sizing Intelligence Widget
        # Baseline Return Rate: 23.2% -> Target: ~14.5% (-37.5% relative reduction)
        # Sample size: 1,500 apparel orders per variant
        cohort_sizing = self.simulate_proportion_experiment(
            experiment_name="EXP-01: Fit & Sizing Intelligence Widget",
            metric_name="Apparel Item Return Rate",
            n_control=1500,
            n_treatment=1500,
            baseline_rate=0.232,
            relative_lift=-0.35,  # 35% relative reduction in returns
        )
        results["EXP-01"] = cohort_sizing.result

        # 2. 1-Click Express Checkout & Digital Wallets
        # Baseline Checkout Completion Rate: 10.98% -> Target: ~22.0% (+100% relative lift)
        # Sample size: 2,000 checkout starts per variant
        cohort_checkout = self.simulate_proportion_experiment(
            experiment_name="EXP-02: 1-Click Express Checkout & Digital Wallets",
            metric_name="Checkout Completion Rate",
            n_control=2000,
            n_treatment=2000,
            baseline_rate=0.1098,
            relative_lift=0.65,  # 65% relative lift in completion
        )
        results["EXP-02"] = cohort_checkout.result

        # 3. Semantic Search & Synonym Expansion
        # Baseline Search Click-Through Rate: 14.04% -> Target: ~35.0% (+150% relative lift)
        # Sample size: 1,200 search sessions per variant
        cohort_search = self.simulate_proportion_experiment(
            experiment_name="EXP-03: Semantic Search & Dynamic Synonym Expansion",
            metric_name="Search Click-Through Rate (CTR)",
            n_control=1200,
            n_treatment=1200,
            baseline_rate=0.1404,
            relative_lift=1.20,  # 120% relative lift in search CTR
        )
        results["EXP-03"] = cohort_search.result

        return results
