"""RICE prioritisation engine for ThreadIQ fashion e-commerce product opportunities."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd


class PrioritizationTier(str, Enum):
    """Execution tiers for product backlog items."""

    NOW = "Now"      # Immediate sprint cycle / current quarter
    NEXT = "Next"    # Following quarter / next planned cycle
    LATER = "Later"  # Backlog / requires further research or lower priority


@dataclass
class RICEOpportunity:
    """Individual product feature or intervention evaluated using RICE scoring."""

    opportunity_id: str
    area: str  # Storefront, Inbound, Outbound
    problem_statement: str
    proposed_feature: str
    reach: int  # Estimated users/sessions/orders impacted per quarter
    impact: float  # 3.0 = Massive, 2.0 = High, 1.0 = Medium, 0.5 = Low, 0.25 = Minimal
    confidence: float  # 1.0 = High (100%), 0.8 = Medium (80%), 0.5 = Low (50%)
    effort: float  # Person-months or sprint units (minimum 0.5)
    rationale: str
    priority_tier: Optional[PrioritizationTier] = None
    rice_score: float = field(init=False)

    def __post_init__(self):
        """Calculate RICE score upon initialization."""
        if self.effort <= 0:
            raise ValueError("Effort must be strictly greater than 0.")
        if not (0.0 < self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0 and 1.0.")
        if self.reach < 0:
            raise ValueError("Reach cannot be negative.")

        self.rice_score = round(
            (float(self.reach) * float(self.impact) * float(self.confidence)) / float(self.effort),
            2,
        )


class RICEPrioritizer:
    """Manager for scoring, ranking, and organizing product backlog opportunities."""

    def __init__(self):
        self._opportunities: List[RICEOpportunity] = []

    def add_opportunity(self, opportunity: RICEOpportunity) -> None:
        """Register a new product opportunity."""
        self._opportunities.append(opportunity)

    def rank(self) -> List[RICEOpportunity]:
        """Rank all opportunities descending by RICE score and assign tiers if unset.

        Tier Assignment Heuristic (unless manually assigned):
        - Top 30% of ranked list -> NOW
        - Next 40% of ranked list -> NEXT
        - Bottom 30% of ranked list -> LATER
        """
        sorted_opps = sorted(self._opportunities, key=lambda x: x.rice_score, reverse=True)
        n = len(sorted_opps)

        if n == 0:
            return []

        for idx, opp in enumerate(sorted_opps):
            if opp.priority_tier is None:
                percentile = idx / n
                if percentile < 0.35:
                    opp.priority_tier = PrioritizationTier.NOW
                elif percentile < 0.70:
                    opp.priority_tier = PrioritizationTier.NEXT
                else:
                    opp.priority_tier = PrioritizationTier.LATER

        self._opportunities = sorted_opps
        return self._opportunities

    def to_dataframe(self) -> pd.DataFrame:
        """Export ranked opportunities to a clean Pandas DataFrame."""
        ranked = self.rank()
        records = []
        for idx, o in enumerate(ranked, start=1):
            records.append({
                "Rank": idx,
                "ID": o.opportunity_id,
                "Area": o.area,
                "Problem": o.problem_statement,
                "Proposed Feature": o.proposed_feature,
                "Reach": o.reach,
                "Impact": o.impact,
                "Confidence": f"{int(o.confidence * 100)}%",
                "Effort": o.effort,
                "RICE Score": o.rice_score,
                "Tier": o.priority_tier.value if o.priority_tier else "Unassigned",
                "Rationale": o.rationale,
            })
        return pd.DataFrame(records)

    def to_markdown_table(self) -> str:
        """Render ranked opportunities as a GitHub-flavored Markdown table."""
        df = self.to_dataframe()
        return df.to_markdown(index=False)
