# ThreadIQ — Assumptions, Limitations & Data Quality Audit

## 1. Data Gaps and Synthetic Data Plan

### Identified Data Gaps
1. **Clickstream and Funnel Telemetry:** Public e-commerce datasets (including Olist) record final transactions but lack top-of-funnel browsing events (impressions, product detail page views, add-to-cart clicks, cart abandonment, and checkout funnel drops).
2. **Search Discovery Events:** No search query logs, query latency, zero-result frequencies, or search click-throughs exist in public transactional dumps.
3. **Daily Inventory & Stock Snapshots:** Olist does not track warehouse stock levels, safety stock thresholds, inventory holding costs, or stockout events over time.
4. **Promotion and Discount Calendars:** Transactional prices exist, but promotional campaign schedules, markdown depths, and coupon codes are unrecorded.
5. **Fashion-Specific Return Drivers:** While Olist records order cancellations and customer review text, it does not provide structured return reason codes typical of apparel retail (e.g., size too small, size too large, fabric dissatisfaction, color variance).

### Synthetic Dataset Design & Honesty Principles
All synthetic tables are generated with fixed pseudo-random seeds (`RANDOM_SEED = 42`) and carry a mandatory column `data_source = 'synthetic'`. Under no circumstances are synthetic metrics merged with observed data without transparent labelling.

| Synthetic Entity | Target Table | Generation Logic & Statistical Assumptions |
| :--- | :--- | :--- |
| **Clickstream Events** | `fct_events_clickstream` | - Converted sessions back-propagate from real `fct_orders` timestamps.<br>- Non-converting sessions generated using realistic e-commerce drop-off rates (e.g., 65% drop between impression and view, 70% drop from view to cart, 50% drop from cart to checkout).<br>- Devices distributed as 65% Mobile, 30% Desktop, 5% Tablet. |
| **Search Queries** | `fct_search_queries` | - Query terms generated from fashion product attributes (`styles.csv` tokens: colors, categories, article types).<br>- Intentional out-of-catalog and misspelled tokens injected at an 8% zero-result rate. |
| **Inventory Snapshots** | `fct_inventory_snapshots` | - Daily snapshots over a 90-day rolling window.<br>- Initial stock-on-hand scaled to trailing SKU velocity; depleted daily by order transactions.<br>- Stockout flag triggered when `available_stock <= 0`.<br>- Replenishment heuristics: critical reorder flag when $\text{Days of Cover} < 7\text{ days}$. |
| **Promotions** | `fct_promotions` | - Markdown tiers (10%, 20%, 30%, 50%) applied across seasonal fashion categories (e.g., end-of-season clearance). |
| **Fashion Return Reasons** | `fct_order_items.return_reason_code` | - Assigned to canceled orders and low-rating reviews (`review_score` 1 and 2):<br>  - 50% `SIZE_FIT`<br>  - 25% `QUALITY_FABRIC`<br>  - 15% `STYLE_NOT_AS_PICTURED`<br>  - 10% `LOGISTICS_DELAY` |

---

## 2. Data Quality Audit & Validation Rules

ThreadIQ enforces seven core data validation checks:

### Check 1: Missing Value Tolerances
- **Mandatory Non-Null:** Primary keys (`order_id`, `customer_id`, `product_id`, `seller_id`), `purchase_timestamp`, `price`, `freight_value`.
- **Allowed Nulls with Business Meaning:**
  - `order_delivered_customer_date`: NULL allowed for canceled, in-transit, or processing orders.
  - `review_comment_message`: NULL allowed (ratings can be submitted without text comments).

### Check 2: Deduplication Assertions
- `customer_id` must be unique in `dim_customers`.
- `order_id` must be unique in `fct_orders`.
- `(order_id, order_item_id)` composite must be strictly unique in `fct_order_items`.
- `review_id` must be unique in `fct_order_reviews`.

### Check 3: Timestamp Consistency & Ordering
- `order_approved_at >= purchase_timestamp` (or within allowable grace period for delayed approval).
- `dispatched_at >= purchase_timestamp`.
- `delivered_customer_date >= dispatched_at`.
- Any record violating chronological order is flagged as `INVALID_TIMESTAMP_CORRUPTION` and isolated.

### Check 4: Referential Integrity
- All `customer_id` values in `fct_orders` must exist in `dim_customers`.
- All `order_id` values in `fct_order_items` must exist in `fct_orders`.
- All `product_id` values in `fct_order_items` must exist in `dim_products`.
- All `seller_id` values in `fct_order_items` must exist in `dim_sellers`.

### Check 5: Domain Boundary Assertions
- `price >= 0.0` (zero price permitted only for promotional gifts; negative prices rejected).
- `freight_value >= 0.0`.
- `review_score BETWEEN 1 AND 5`.
- `stock_on_hand >= 0`.
- `catalog_completeness_score BETWEEN 0 AND 100`.

### Check 6: Valid Categorical Enums
- `order_status` in `['delivered', 'shipped', 'canceled', 'unavailable', 'invoiced', 'processing', 'created', 'approved']`.
- `return_reason_code` in `['SIZE_FIT', 'QUALITY_FABRIC', 'STYLE_NOT_AS_PICTURED', 'LOGISTICS_DELAY']`.

### Check 7: Funnel Step Monotonicity
- Total Funnel Volumes must satisfy:
  $$\text{Impressions} \ge \text{Product Views} \ge \text{Add-to-Carts} \ge \text{Checkout Starts} \ge \text{Purchases}$$

---

## 3. Assumptions and Limitations

1. **Simulated Marketplace Context:** ThreadIQ is an independent product intelligence demonstration and is **not an official Myntra system**.
2. **Reconciliation Mapping:** Olist is a Brazilian marketplace with Portuguese product titles, while the Fashion dataset originates from an Indian fashion catalog. The unified data model reconciles transactions by mapping order mechanics to fashion taxonomy.
3. **Observational vs. Causal Uplift:** Differences in conversion across cohorts in historical public data are purely correlational. No causal claims are made unless derived from explicit, controlled A/B test experiments.
4. **Local Workstation Constraint:** The entire pipeline and database run locally on SQLite without requiring distributed compute clusters (Spark/Presto) or paid cloud warehouses.
