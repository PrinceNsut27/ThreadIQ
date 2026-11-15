"""Common utilities and base classes for ThreadIQ analytics."""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sqlalchemy.engine import Engine

from src.threadiq.data.loaders import get_db_engine, query_to_df
from src.threadiq.utils.helpers import safe_divide


@dataclass
class MetricResult:
    """Standard container for an analytics metric."""
    name: str
    value: float | int | str
    formatted_value: str
    numerator: float | int | None = None
    denominator: float | int | None = None
    unit: str = ""
    provenance: str = "observed"  # 'observed' | 'synthetic' | 'reconciled'
    notes: str = ""


class BaseAnalytics:
    """Base class for all ThreadIQ domain analytics engines."""

    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_db_engine()

    def query(self, sql_str: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
        """Execute SQL query and return a DataFrame."""
        return query_to_df(sql_str, engine=self.engine, params=params)

    @staticmethod
    def calc_rate(
        numerator: float | int,
        denominator: float | int,
        as_percentage: bool = True,
        decimals: int = 2,
    ) -> float:
        """Safely calculate a conversion or failure rate with division-by-zero protection."""
        val = safe_divide(numerator, denominator, default=0.0)
        if as_percentage:
            val *= 100.0
        return round(val, decimals)
