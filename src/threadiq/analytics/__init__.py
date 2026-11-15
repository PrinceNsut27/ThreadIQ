"""ThreadIQ Product Analytics Package."""

from src.threadiq.analytics.common import BaseAnalytics, MetricResult
from src.threadiq.analytics.inbound import (
    CatalogAnalytics,
    InventoryAnalytics,
    PricingPromotionsAnalytics,
    ReplenishmentAnalytics,
)
from src.threadiq.analytics.outbound import (
    CancellationReturnAnalytics,
    DeliveryPerformanceAnalytics,
    FulfillmentAnalytics,
    OperationalInsightsAnalytics,
)
from src.threadiq.analytics.storefront import (
    CustomerAnalytics,
    FunnelAnalytics,
    ProductPerformanceAnalytics,
    SearchAnalytics,
)

__all__ = [
    "BaseAnalytics",
    "MetricResult",
    "FunnelAnalytics",
    "SearchAnalytics",
    "ProductPerformanceAnalytics",
    "CustomerAnalytics",
    "CatalogAnalytics",
    "InventoryAnalytics",
    "PricingPromotionsAnalytics",
    "ReplenishmentAnalytics",
    "FulfillmentAnalytics",
    "DeliveryPerformanceAnalytics",
    "CancellationReturnAnalytics",
    "OperationalInsightsAnalytics",
]
