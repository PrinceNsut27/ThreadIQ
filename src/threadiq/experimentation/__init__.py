"""ThreadIQ Experimentation & Decision Intelligence Package.

Provides statistical testing, sample size estimation, RICE prioritisation,
and A/B test simulation tools for fashion e-commerce product decision-making.
"""

from src.threadiq.experimentation.calculator import (
    ExperimentConfig,
    ExperimentResult,
    SampleAnalysis,
    calculate_sample_size_proportions,
    calculate_sample_size_continuous,
    calculate_minimum_detectable_effect,
    two_proportion_z_test,
    difference_in_means_test,
)
from src.threadiq.experimentation.prioritization import (
    RICEOpportunity,
    RICEPrioritizer,
    PrioritizationTier,
)
from src.threadiq.experimentation.simulation import (
    ExperimentSimulator,
    SimulatedCohort,
)

__all__ = [
    "ExperimentConfig",
    "ExperimentResult",
    "SampleAnalysis",
    "calculate_sample_size_proportions",
    "calculate_sample_size_continuous",
    "calculate_minimum_detectable_effect",
    "two_proportion_z_test",
    "difference_in_means_test",
    "RICEOpportunity",
    "RICEPrioritizer",
    "PrioritizationTier",
    "ExperimentSimulator",
    "SimulatedCohort",
]
