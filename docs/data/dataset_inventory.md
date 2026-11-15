# ThreadIQ — Dataset Inventory & Data Lineage

This inventory categorizes all data assets utilized across ThreadIQ, detailing their origin, licence, and purpose.

---

## 1. Observed Public Datasets

### A. Olist Brazilian E-Commerce Dataset
- **Source**: Kaggle (`olistbr/brazilian-ecommerce`)
- **Licence**: CC BY-NC-SA 4.0
- **Scope & Role**: Core transactional and operational backbone.
- **Key Tables**:
  - `olist_orders_dataset.csv`: Order lifecycle timestamps, statuses.
  - `olist_order_items_dataset.csv`: Purchased item prices, freight, seller IDs.
  - `olist_customers_dataset.csv`: Customer IDs, unique customer IDs, states, zip codes.
  - `olist_order_payments_dataset.csv`: Payment types, installments, transaction values.
  - `olist_order_reviews_dataset.csv`: Review scores, timestamps.
  - `olist_sellers_dataset.csv`: Merchant locations.
- **Lineage Tag**: `[OBSERVED]`

### B. Fashion Product Images Dataset
- **Source**: Kaggle (`paramaggarwal/fashion-product-images-dataset`)
- **Licence**: CC0: Public Domain
- **Scope & Role**: Apparel catalog attributes and merchandising hierarchy.
- **Key Fields**: `masterCategory`, `subCategory`, `articleType`, `baseColour`, `season`, `usage`, `productDisplayName`.
- **Lineage Tag**: `[OBSERVED]`

---

## 2. Synthetic Data Streams

Because public e-commerce datasets omit top-of-funnel web sessions and daily warehouse inventory snapshots, ThreadIQ incorporates a stochastic behavioral generator (`src/threadiq/data/synthetic.py`):

1. **Clickstream Event Stream (`fct_sessions`, `fct_events_clickstream`)**:
   - Monotonically sequenced user journeys across 6 funnel stages.
   - Lineage Tag: `[SYNTHETIC]`
2. **Search Query Logs (`fct_search_queries`)**:
   - Query text, results returned count, clicks, and zero-result flags.
   - Lineage Tag: `[SYNTHETIC]`
3. **Daily Inventory Time-Series (`fct_inventory_snapshots`)**:
   - Daily snapshots across 4 demand archetypes (`FAST_MOVER`, `STEADY_STAPLE`, `SLOW_MOVER`, `SEASONAL_SURGE`).
   - Lineage Tag: `[SYNTHETIC]`
4. **Marketing Promotional Calendars (`fct_promotions`)**:
   - Campaign types, start/end dates, and discount depths.
   - Lineage Tag: `[SYNTHETIC]`
