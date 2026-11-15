"""Statistical calculation engine for A/B testing and experimentation in ThreadIQ."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration parameters for an A/B experimentation test."""

    name: str
    primary_kpi: str
    baseline_conversion: float
    mde_relative: float
    alpha: float = 0.05
    power: float = 0.80
    hypothesis: str = ""
    control_name: str = "Control (A)"
    treatment_name: str = "Treatment (B)"


@dataclass(frozen=True)
class SampleAnalysis:
    """Sample size requirements for an A/B test variant."""

    required_sample_size_per_variant: int
    total_required_sample_size: int
    baseline_rate: float
    expected_treatment_rate: float
    relative_mde_percent: float
    absolute_mde: float
    alpha: float
    power: float
    estimated_days_to_complete: Optional[float] = None


@dataclass(frozen=True)
class ExperimentResult:
    """Statistical evaluation of an executed A/B experiment."""

    experiment_name: str
    metric_name: str
    control_count: int
    control_conversions: int
    control_rate: float
    treatment_count: int
    treatment_conversions: int
    treatment_rate: float
    absolute_lift: float
    relative_lift_percent: float
    p_value: float
    z_statistic: float
    ci_lower: float
    ci_upper: float
    is_statistically_significant: bool
    alpha: float
    power: float
    sample_ratio_mismatch_detected: bool = False
    srm_p_value: float = 1.0
    provenance: str = "simulated_experiment"
    notes: str = ""


def calculate_sample_size_proportions(
    baseline_conversion: float,
    relative_mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    daily_traffic: Optional[int] = None,
) -> SampleAnalysis:
    """Calculate required sample size per variant for a two-sample proportion test.

    Args:
        baseline_conversion: Current conversion rate as a proportion in (0, 1), e.g. 0.05.
        relative_mde: Minimum Detectable Effect as a relative proportion, e.g. 0.10 for +10% lift.
        alpha: Significance level (default 0.05 for 95% confidence).
        power: Statistical power 1 - beta (default 0.80 for 80% power).
        daily_traffic: Optional total daily visitor count to estimate duration in days.

    Returns:
        SampleAnalysis object with variant and total sample size requirements.
    """
    if not (0.0 < baseline_conversion < 1.0):
        raise ValueError("baseline_conversion must be strictly between 0 and 1.")
    if relative_mde == 0:
        raise ValueError("relative_mde cannot be zero.")
    if not (0.0 < alpha < 1.0) or not (0.0 < power < 1.0):
        raise ValueError("alpha and power must be strictly between 0 and 1.")

    p1 = float(baseline_conversion)
    p2 = float(baseline_conversion * (1.0 + relative_mde))
    p2 = max(0.0001, min(0.9999, p2))

    delta = abs(p2 - p1)
    p_bar = (p1 + p2) / 2.0

    z_alpha = stats.norm.ppf(1.0 - (alpha / 2.0))
    z_beta = stats.norm.ppf(power)

    # Standard formula for two-sample proportion test
    numerator = (
        z_alpha * np.sqrt(2.0 * p_bar * (1.0 - p_bar))
        + z_beta * np.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2))
    ) ** 2
    denominator = delta ** 2

    n_per_variant = int(np.ceil(numerator / denominator))
    total_n = n_per_variant * 2

    estimated_days = None
    if daily_traffic and daily_traffic > 0:
        estimated_days = round(total_n / daily_traffic, 1)

    return SampleAnalysis(
        required_sample_size_per_variant=n_per_variant,
        total_required_sample_size=total_n,
        baseline_rate=round(p1, 5),
        expected_treatment_rate=round(p2, 5),
        relative_mde_percent=round(relative_mde * 100.0, 2),
        absolute_mde=round(delta, 5),
        alpha=alpha,
        power=power,
        estimated_days_to_complete=estimated_days,
    )


def calculate_sample_size_continuous(
    std_dev: float,
    absolute_mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    daily_traffic: Optional[int] = None,
) -> SampleAnalysis:
    """Calculate sample size per variant for continuous metrics (e.g. Average Order Value).

    Args:
        std_dev: Standard deviation of the continuous metric.
        absolute_mde: Minimum detectable difference in means (e.g. $5.00 lift).
        alpha: Significance level (default 0.05).
        power: Statistical power (default 0.80).
        daily_traffic: Optional daily transaction count.

    Returns:
        SampleAnalysis object with sample size requirements.
    """
    if std_dev <= 0 or absolute_mde <= 0:
        raise ValueError("std_dev and absolute_mde must be positive.")

    z_alpha = stats.norm.ppf(1.0 - (alpha / 2.0))
    z_beta = stats.norm.ppf(power)

    numerator = 2.0 * ((z_alpha + z_beta) ** 2) * (std_dev ** 2)
    denominator = absolute_mde ** 2

    n_per_variant = int(np.ceil(numerator / denominator))
    total_n = n_per_variant * 2

    estimated_days = None
    if daily_traffic and daily_traffic > 0:
        estimated_days = round(total_n / daily_traffic, 1)

    return SampleAnalysis(
        required_sample_size_per_variant=n_per_variant,
        total_required_sample_size=total_n,
        baseline_rate=0.0,
        expected_treatment_rate=round(absolute_mde, 2),
        relative_mde_percent=0.0,
        absolute_mde=round(absolute_mde, 2),
        alpha=alpha,
        power=power,
        estimated_days_to_complete=estimated_days,
    )


def calculate_minimum_detectable_effect(
    sample_size_per_variant: int,
    baseline_conversion: float,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """Estimate the minimum relative detectable effect (%) given an available sample size.

    Args:
        sample_size_per_variant: Available sample size per branch.
        baseline_conversion: Baseline conversion proportion.
        alpha: Significance level.
        power: Statistical power.

    Returns:
        Relative MDE as a percentage (e.g. 12.5 for 12.5% lift).
    """
    if sample_size_per_variant <= 0 or not (0 < baseline_conversion < 1):
        raise ValueError("Invalid sample size or baseline conversion.")

    z_alpha = stats.norm.ppf(1.0 - (alpha / 2.0))
    z_beta = stats.norm.ppf(power)
    p = baseline_conversion

    # Approximate absolute delta
    delta_abs = (z_alpha + z_beta) * np.sqrt(2.0 * p * (1.0 - p) / sample_size_per_variant)
    relative_mde_pct = (delta_abs / p) * 100.0
    return round(float(relative_mde_pct), 2)


def check_sample_ratio_mismatch(
    control_count: int,
    treatment_count: int,
    expected_ratio: float = 0.5,
    alpha: float = 0.001,
) -> Tuple[bool, float]:
    """Test for Sample Ratio Mismatch (SRM) using a Chi-square goodness-of-fit test.

    Args:
        control_count: Number of visitors assigned to Control.
        treatment_count: Number of visitors assigned to Treatment.
        expected_ratio: Target split ratio for Control (default 0.5 for 50/50).
        alpha: Stringent alpha threshold for SRM detection (default 0.001).

    Returns:
        Tuple of (srm_detected: bool, p_value: float).
    """
    total = control_count + treatment_count
    if total <= 0:
        return False, 1.0

    expected_control = total * expected_ratio
    expected_treatment = total * (1.0 - expected_ratio)

    observed = [control_count, treatment_count]
    expected = [expected_control, expected_treatment]

    chi2, p_val = stats.chisquare(f_obs=observed, f_exp=expected)
    srm_detected = bool(p_val < alpha)
    return srm_detected, float(p_val)


def two_proportion_z_test(
    control_conversions: int,
    control_count: int,
    treatment_conversions: int,
    treatment_count: int,
    alpha: float = 0.05,
    experiment_name: str = "A/B Experiment",
    metric_name: str = "Conversion Rate",
    provenance: str = "simulated_experiment",
) -> ExperimentResult:
    """Perform a two-proportion z-test to compare conversion rates between Control and Treatment.

    Computes two-tailed p-value, z-statistic, confidence intervals, relative lift,
    and conducts an automated Sample Ratio Mismatch (SRM) verification.

    Args:
        control_conversions: Successful events in Control group.
        control_count: Total sample size in Control group.
        treatment_conversions: Successful events in Treatment group.
        treatment_count: Total sample size in Treatment group.
        alpha: Significance level (default 0.05).
        experiment_name: Descriptive name of the experiment.
        metric_name: Name of evaluated primary KPI.
        provenance: Data source label (default 'simulated_experiment').

    Returns:
        ExperimentResult object with comprehensive statistical analysis.
    """
    if control_count <= 0 or treatment_count <= 0:
        raise ValueError("Sample sizes must be strictly positive.")
    if control_conversions < 0 or treatment_conversions < 0:
        raise ValueError("Conversions cannot be negative.")
    if control_conversions > control_count or treatment_conversions > treatment_count:
        raise ValueError("Conversions cannot exceed total sample size.")

    p_ctrl = control_conversions / control_count
    p_trt = treatment_conversions / treatment_count

    abs_lift = p_trt - p_ctrl
    rel_lift = (abs_lift / p_ctrl * 100.0) if p_ctrl > 0 else 0.0

    # Pooled proportion for z-statistic under H0: p1 == p2
    total_conversions = control_conversions + treatment_conversions
    total_count = control_count + treatment_count
    p_pooled = total_conversions / total_count

    se_pooled = np.sqrt(p_pooled * (1.0 - p_pooled) * (1.0 / control_count + 1.0 / treatment_count))
    z_stat = (p_trt - p_ctrl) / se_pooled if se_pooled > 0 else 0.0

    p_val = float(stats.norm.sf(abs(z_stat)) * 2.0)

    # Unpooled standard error for confidence interval of the difference (p_trt - p_ctrl)
    se_diff = np.sqrt(
        (p_ctrl * (1.0 - p_ctrl) / control_count) + (p_trt * (1.0 - p_trt) / treatment_count)
    )
    z_crit = stats.norm.ppf(1.0 - (alpha / 2.0))
    ci_lower = abs_lift - (z_crit * se_diff)
    ci_upper = abs_lift + (z_crit * se_diff)

    is_sig = bool(p_val < alpha)

    # SRM check
    srm_detected, srm_p_val = check_sample_ratio_mismatch(control_count, treatment_count)

    notes = "Statistically significant lift detected." if is_sig else "No statistically significant difference."
    if srm_detected:
        notes += f" WARNING: Sample Ratio Mismatch (SRM) detected (p={srm_p_val:.4e}). Results may be biased."

    return ExperimentResult(
        experiment_name=experiment_name,
        metric_name=metric_name,
        control_count=control_count,
        control_conversions=control_conversions,
        control_rate=round(p_ctrl, 4),
        treatment_count=treatment_count,
        treatment_conversions=treatment_conversions,
        treatment_rate=round(p_trt, 4),
        absolute_lift=round(abs_lift, 4),
        relative_lift_percent=round(rel_lift, 2),
        p_value=round(p_val, 6),
        z_statistic=round(z_stat, 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
        is_statistically_significant=is_sig,
        alpha=alpha,
        power=0.80,
        sample_ratio_mismatch_detected=srm_detected,
        srm_p_value=round(srm_p_val, 6),
        provenance=provenance,
        notes=notes,
    )


def difference_in_means_test(
    control_values: Union[np.ndarray, pd.Series, list],
    treatment_values: Union[np.ndarray, pd.Series, list],
    alpha: float = 0.05,
    experiment_name: str = "A/B Continuous Experiment",
    metric_name: str = "Continuous Metric (AOV)",
    provenance: str = "simulated_experiment",
) -> ExperimentResult:
    """Perform Welch's two-sample independent t-test for continuous metrics (unequal variance).

    Args:
        control_values: Array of continuous observations for Control.
        treatment_values: Array of continuous observations for Treatment.
        alpha: Significance level (default 0.05).
        experiment_name: Name of the experiment.
        metric_name: Metric evaluated.
        provenance: Data lineage tag.

    Returns:
        ExperimentResult object.
    """
    ctrl = np.asarray(control_values, dtype=float)
    trt = np.asarray(treatment_values, dtype=float)

    n_ctrl = len(ctrl)
    n_trt = len(trt)
    if n_ctrl < 2 or n_trt < 2:
        raise ValueError("Need at least 2 observations per variant for a t-test.")

    mean_ctrl = float(np.mean(ctrl))
    mean_trt = float(np.mean(trt))

    abs_lift = mean_trt - mean_ctrl
    rel_lift = (abs_lift / mean_ctrl * 100.0) if mean_ctrl != 0 else 0.0

    t_stat, p_val = stats.ttest_ind(trt, ctrl, equal_var=False)

    # Degrees of freedom for Welch-Satterthwaite
    s1_sq = float(np.var(ctrl, ddof=1))
    s2_sq = float(np.var(trt, ddof=1))
    se_diff = np.sqrt((s1_sq / n_ctrl) + (s2_sq / n_trt))

    df_denom = ((s1_sq / n_ctrl) ** 2) / (n_ctrl - 1) + ((s2_sq / n_trt) ** 2) / (n_trt - 1)
    df = (se_diff ** 4) / df_denom if df_denom > 0 else (n_ctrl + n_trt - 2)

    t_crit = stats.t.ppf(1.0 - (alpha / 2.0), df=df)
    ci_lower = abs_lift - (t_crit * se_diff)
    ci_upper = abs_lift + (t_crit * se_diff)

    is_sig = bool(p_val < alpha)

    srm_detected, srm_p_val = check_sample_ratio_mismatch(n_ctrl, n_trt)
    notes = "Statistically significant difference in means." if is_sig else "No significant difference in means."

    return ExperimentResult(
        experiment_name=experiment_name,
        metric_name=metric_name,
        control_count=n_ctrl,
        control_conversions=int(np.sum(ctrl > 0)),
        control_rate=round(mean_ctrl, 2),
        treatment_count=n_trt,
        treatment_conversions=int(np.sum(trt > 0)),
        treatment_rate=round(mean_trt, 2),
        absolute_lift=round(abs_lift, 2),
        relative_lift_percent=round(rel_lift, 2),
        p_value=round(float(p_val), 6),
        z_statistic=round(float(t_stat), 4),
        ci_lower=round(ci_lower, 2),
        ci_upper=round(ci_upper, 2),
        is_statistically_significant=is_sig,
        alpha=alpha,
        power=0.80,
        sample_ratio_mismatch_detected=srm_detected,
        srm_p_value=round(srm_p_val, 6),
        provenance=provenance,
        notes=notes,
    )
