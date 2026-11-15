# ThreadIQ — Product Metrics Dictionary

This document serves as the enterprise standard metric catalog for ThreadIQ across **Storefront Intelligence**, **Inbound Supply Chain**, and **Outbound Logistics & Reverse Supply Chain**. Every metric is rigorously documented with formal mathematical formulas, numerator/denominator specifications, exact data source tables, data provenance classifications, business interpretations, and known limitations.

---

## 1. Storefront Product Analytics Metrics

### 1.1 Stage Conversion Rate (`stage_conversion_rate`)
* **Definition:** The percentage of digital shopping sessions that successfully progress from the immediate previous funnel milestone to the current funnel milestone.
* **Mathematical Formula:**
  $$CR_i = \left( \frac{\text{Sessions reaching Stage } i}{\text{Sessions reaching Stage } i-1} \right) \times 100$$
* **Numerator:** Distinct count of `session_id` reaching Stage $i$.
* **Denominator:** Distinct count of `session_id` reaching Stage $i-1$.
* **Data Source:** `fct_events`, `fct_sessions`.
* **Data Provenance:** **Synthetic Data** (generated via stochastic state-machine transition simulation in `src/threadiq/data/synthetic.py`).
* **Business Interpretation:** Isolates granular user journey drop-offs (e.g., discovering whether conversion leakage is concentrated at the PDP-to-cart transition or the cart-to-checkout step).
* **Target Benchmark:** PDP-to-Cart $\ge 15.0\%$; Cart-to-Checkout $\ge 50.0\%$; Checkout-to-Purchase $\ge 70.0\%$.
* **Known Limitations:** Does not account for cross-device session bridging where a user browses on mobile and purchases later on desktop under a distinct session ID.

---

### 1.2 Cumulative Conversion Rate (`cumulative_conversion_rate`)
* **Definition:** The proportion of total starting sessions that successfully culminate in an order purchase, evaluated from top-of-funnel (Homepage Impression).
* **Mathematical Formula:**
  $$CR_{\text{cum}, i} = \left( \frac{\text{Sessions reaching Stage } i}{\text{Total Initial Sessions (Stage 1)}} \right) \times 100$$
* **Numerator:** Distinct count of `session_id` active at Stage $i$.
* **Denominator:** Total distinct count of `session_id` recorded at Stage 1 (`homepage_impression`).
* **Data Source:** `fct_events`, `fct_sessions`.
* **Data Provenance:** **Synthetic Data** (stochastic simulation).
* **Business Interpretation:** Macro efficiency KPI of the entire digital storefront experience. Represents the ultimate yield of paid and organic acquisition traffic.
* **Target Benchmark:** Fashion e-commerce benchmark: $2.0\% - 3.5\%$. ThreadIQ baseline: **1.82%**.
* **Known Limitations:** Treats all sessions equally regardless of user acquisition intent (e.g., high-intent direct traffic vs. casual social media browsing).

---

### 1.3 Cart Abandonment Rate (`cart_abandonment_rate`)
* **Definition:** The percentage of shopping sessions where at least one item was added to the bag, but no final purchase was completed.
* **Mathematical Formula:**
  $$CAR = \left( \frac{\text{Sessions}_{\text{add\_to\_cart}} - \text{Sessions}_{\text{purchase}}}{\text{Sessions}_{\text{add\_to\_cart}}} \right) \times 100$$
* **Numerator:** Sessions containing an `add_to_cart` event minus sessions containing a `purchase_completed` event.
* **Denominator:** Total count of sessions with at least one `add_to_cart` event.
* **Data Source:** `fct_events`.
* **Data Provenance:** **Synthetic Data** (stochastic simulation).
* **Business Interpretation:** Measures high-intent commercial leakage. Reflects checkout form friction, unexpected shipping fees, sizing uncertainty, and absence of preferred payment methods.
* **Target Benchmark:** Fashion industry benchmark: $70.0\% - 75.0\%$. ThreadIQ baseline: **93.25%** (identifying acute checkout friction).
* **Known Limitations:** Cannot distinguish intentional cart abandonment from shoppers using the cart as a temporary wishlist for future consideration.

---

### 1.4 Search Click-Through Rate (`search_click_through_rate`)
* **Definition:** The percentage of catalog search queries that result in at least one product detail page (PDP) click.
* **Mathematical Formula:**
  $$CTR_{\text{search}} = \left( \frac{\text{Search Queries with } \ge 1 \text{ Clicked Product}}{\text{Total Search Queries Executed}} \right) \times 100$$
* **Numerator:** Count of `fct_search_queries` records where `clicked_product_id IS NOT NULL`.
* **Denominator:** Total count of `fct_search_queries` records.
* **Data Source:** `fct_search_queries`.
* **Data Provenance:** **Synthetic Data** (simulated search log distributions).
* **Business Interpretation:** Direct measurement of search relevance, ranking precision, and catalog vocabulary matching.
* **Target Benchmark:** $\ge 35.0\%$. ThreadIQ baseline: **14.04%**.
* **Known Limitations:** Clicks do not necessarily reflect customer satisfaction; clickbait images or inaccurate titles can produce high CTR with immediate bounce.

---

### 1.5 Zero-Result Search Rate (`zero_result_search_rate`)
* **Definition:** The proportion of user-submitted search queries that return zero matching products from the catalog.
* **Mathematical Formula:**
  $$ZRSR = \left( \frac{\text{Search Queries with } \text{results\_count} = 0}{\text{Total Search Queries Executed}} \right) \times 100$$
* **Numerator:** Count of `fct_search_queries` records where `results_count = 0`.
* **Denominator:** Total count of `fct_search_queries` records.
* **Data Source:** `fct_search_queries`.
* **Data Provenance:** **Synthetic Data** (simulated search log distributions).
* **Business Interpretation:** Identifies unmet customer demand, missing catalog synonyms, spelling sensitivity failures, and true merchandise assortment gaps.
* **Target Benchmark:** $< 10.0\%$. ThreadIQ baseline: **85.96%** (severe discovery failure on natural language fashion queries).
* **Known Limitations:** Does not distinguish between user typos, unstocked product lines, and overly specific compound queries (e.g., *"vintage red velvet winter jacket size s"*).

---

### 1.6 Customer Repeat Purchase Rate (`repeat_purchase_rate`)
* **Definition:** The percentage of unique customers who have completed two or more distinct orders across their lifetime.
* **Mathematical Formula:**
  $$RPR = \left( \frac{\text{Unique Customers with Lifetime Orders } \ge 2}{\text{Total Unique Customers with } \ge 1 \text{ Order}} \right) \times 100$$
* **Numerator:** Count of `customer_unique_id` with `COUNT(order_id) >= 2`.
* **Denominator:** Count of `customer_unique_id` with `COUNT(order_id) >= 1`.
* **Data Source:** `dim_customers`, `fct_orders`.
* **Data Provenance:** **Observed Public Data** (Olist Brazilian E-Commerce dataset).
* **Business Interpretation:** Primary indicator of product satisfaction, post-purchase fulfillment reliability, and sustainable customer lifetime value (LTV).
* **Target Benchmark:** Apparel benchmark: $25.0\% - 30.0\%$. ThreadIQ baseline: **3.1%** (reflecting typical marketplace solo-purchase dynamics).
* **Known Limitations:** In marketplaces with long inter-purchase cycles, trailing 12-month windows may underestimate eventual lifetime repeat rates.

---

### 1.7 Average Order Value (`average_order_value`)
* **Definition:** The mean monetary transaction value generated per completed customer order.
* **Mathematical Formula:**
  $$\text{AOV} = \frac{\sum_{i=1}^{N_{\text{orders}}} (\text{price}_i + \text{freight}_i)}{N_{\text{orders}}}$$
* **Numerator:** Cumulative monetary sum of item prices and freight charges across valid, non-canceled orders.
* **Denominator:** Total count of completed, non-canceled orders ($N_{\text{orders}}$).
* **Data Source:** `fct_orders`, `fct_order_items`.
* **Data Provenance:** **Observed Public Data** (Olist dataset).
* **Business Interpretation:** Governs unit economics, CAC payback thresholds, and shipping threshold promotions.
* **Target Benchmark:** Sustained commercial margin: $\ge \$100.00$. ThreadIQ baseline: **$137.41**.
* **Known Limitations:** Can be heavily skewed by high-value outliers (e.g., bulk business orders or jewelry items); median order value should be consulted in parallel.

---

## 2. Inbound Supply Chain Analytics Metrics

### 2.1 Catalog Completeness Score (`catalog_completeness_score`)
* **Definition:** The percentage of mandatory merchandising attributes (`article_type`, `sub_category`, `base_colour`, `season`, `usage`) populated with valid, non-null values.
* **Mathematical Formula:**
  $$S_j = \left( \frac{\sum_{k=1}^5 \mathbb{I}(\text{attribute}_{j,k} \ne \text{null})}{5} \right) \times 100$$
* **Numerator:** Count of non-null mandatory attributes for product $j$.
* **Denominator:** Total count of mandatory attributes (5).
* **Data Source:** `dim_products`.
* **Data Provenance:** **Reconciled Data** (Fashion Product Images Kaggle metadata matched to Olist category taxonomy).
* **Business Interpretation:** Directly impacts organic search discoverability and faceted filter navigation. Incomplete attributes hide products from filtered category views.
* **Target Benchmark:** $100.0\%$. ThreadIQ baseline: **97.2%** (10% of items lack `season` and `usage`).
* **Known Limitations:** Measures field population presence, but does not validate typographical correctness or semantic accuracy of the attribute tags.

---

### 2.2 In-Stock Availability Rate (`in_stock_availability_rate`)
* **Definition:** The proportion of active SKU-days where available physical inventory in the fulfillment center was greater than zero.
* **Mathematical Formula:**
  $$ISAR = \left( \frac{\text{SKU Days with } \text{available\_quantity} > 0}{\text{Total Observed SKU Days}} \right) \times 100$$
* **Numerator:** Count of daily inventory snapshot records where `available_quantity > 0`.
* **Denominator:** Total count of daily snapshot records across all active catalog products.
* **Data Source:** `fct_inventory_snapshots`.
* **Data Provenance:** **Synthetic Data** (daily warehouse inventory snapshot model).
* **Business Interpretation:** Measures operational supply chain continuity and customer merchandise accessibility.
* **Target Benchmark:** $\ge 98.0\%$. ThreadIQ baseline: **92.5%**.
* **Known Limitations:** A SKU may be in-stock overall, but have specific broken sizes (e.g., Medium out of stock while XS remains available).

---

### 2.3 Stockout Rate (`stockout_rate`)
* **Definition:** The proportion of active SKU-days where inventory was completely depleted, rendering the product unpurchasable.
* **Mathematical Formula:**
  $$SOR = 100\% - ISAR = \left( \frac{\text{SKU Days with } \text{available\_quantity} = 0}{\text{Total Observed SKU Days}} \right) \times 100$$
* **Numerator:** Count of daily snapshot records where `available_quantity = 0`.
* **Denominator:** Total active SKU-days.
* **Data Source:** `fct_inventory_snapshots`.
* **Data Provenance:** **Synthetic Data**.
* **Business Interpretation:** Represents direct lost commercial revenue, degraded organic search ranking, and ad spend waste on depleted listings.
* **Target Benchmark:** $\le 2.0\%$. ThreadIQ baseline: **7.5%**.
* **Known Limitations:** Ignores shadow demand (unrecorded traffic bounce when shoppers see an out-of-stock badge).

---

### 2.4 Days of Cover (`days_of_cover` / `DoC`)
* **Definition:** The projected number of days current warehouse inventory will last based on historical sales velocity.
* **Mathematical Formula:**
  $$DoC_j = \frac{\text{Current Available Quantity}_j}{\max(\text{Daily Sales Velocity}_j, 0.1)}$$
* **Numerator:** Current stock on hand in the warehouse for SKU $j$.
* **Denominator:** 30-day average daily unit sales velocity ($V_j$).
* **Data Source:** `fct_inventory_snapshots`, `fct_order_items`.
* **Data Provenance:** **Reconciled Data** (Synthetic inventory balances combined with observed Olist transaction velocity).
* **Business Interpretation:** Governs automated procurement. Identifies imminent stockout risks ($DoC \le 7$ days) versus overstocked working capital traps ($DoC > 60$ days).
* **Target Benchmark:** Fast-fashion target: **14 to 45 days**. ThreadIQ findings: SKU 1101 has critical $DoC = 4.2$ days.
* **Known Limitations:** Assumes linear sales velocity extrapolation; does not incorporate upcoming promotional spikes or seasonal trend inflections.

---

### 2.5 Suggested Replenishment Order Quantity (`suggested_reorder_units`)
* **Definition:** The recommended purchase order quantity required to restore SKU inventory to a standardized 30-day safety cover buffer.
* **Mathematical Formula:**
  $$\text{Reorder Units}_j = \max(0, \lceil (30 - DoC_j) \times V_j \rceil)$$
* **Numerator / Computation:** Days of cover deficit $(30 - DoC_j)$ multiplied by daily sales velocity $V_j$, floored at zero.
* **Data Source:** Computed in `src/threadiq/analytics/inbound/replenishment.py`.
* **Data Provenance:** **Reconciled Analytical Model**.
* **Business Interpretation:** Enables autonomous purchase order generation, removing manual buyer guesswork and preventing stockouts.
* **Target Urgency Tiers:** Critical ($DoC \le 7$d), High ($DoC \le 14$d), Medium ($DoC \le 30$d), Normal ($DoC > 30$d).
* **Known Limitations:** Does not factor in supplier Minimum Order Quantities (MOQs) or container shipping batch sizes.

---

### 2.6 Average Promotional Markdown Depth (`avg_discount_depth`)
* **Definition:** The average percentage price discount applied across active promotional campaigns.
* **Mathematical Formula:**
  $$\overline{\text{Discount}} = \frac{1}{K} \sum_{k=1}^K \text{discount\_percent}_k$$
* **Numerator:** Sum of nominal promotional discount percentage points across campaigns.
* **Denominator:** Total count of active promotional campaigns ($K$).
* **Data Source:** `fct_promotions`.
* **Data Provenance:** **Synthetic Data** (simulated promotional schedule).
* **Business Interpretation:** Monitors gross margin compression and brand equity dilution from excessive flash sale markdowns.
* **Target Benchmark:** Flash Sales $\le 30\%$, Seasonal Clearance $\le 40\%$. ThreadIQ baseline: 43.3% of campaigns are Flash Sales at 30% discount.
* **Known Limitations:** Evaluates nominal campaign markdown, but does not capture stackable customer coupon codes or payment partner cashbacks.

---

## 3. Outbound Supply Chain & Logistics Metrics

### 3.1 On-Time Delivery Rate (`on_time_delivery_rate` / `OTD%`)
* **Definition:** The percentage of customer shipments delivered on or before the committed delivery promise date established at checkout.
* **Mathematical Formula:**
  $$OTD\% = \left( \frac{\text{Delivered Orders with } t_{\text{actual\_delivery}} \le t_{\text{estimated\_delivery}}}{\text{Total Delivered Orders}} \right) \times 100$$
* **Numerator:** Count of delivered orders where `actual_delivery_timestamp <= estimated_delivery_timestamp`.
* **Denominator:** Total count of orders with confirmed customer delivery timestamps.
* **Data Source:** `fct_shipments_deliveries`, `fct_orders`.
* **Data Provenance:** **Observed Public Data** (Olist dataset).
* **Business Interpretation:** Primary operational fulfillment SLA. Breaches directly drive WISMO support tickets, customer dissatisfaction, and order cancellations.
* **Target Benchmark:** Industry standard: $\ge 95.0\%$. ThreadIQ baseline: **91.8%** overall (69.7% on specific legacy routes).
* **Known Limitations:** Relies on carrier milestone scans; carrier failure to scan at delivery can distort timestamp precision.

---

### 3.2 Lead Time Decomposition (Fulfillment vs. Transit Latency)
* **Definition:** The breakdown of total customer fulfillment latency into seller warehouse processing time versus carrier transit duration.
* **Mathematical Formulation:**
  $$T_{\text{total}} = T_{\text{dispatch}} + T_{\text{transit}}$$
  $$T_{\text{dispatch}} = t_{\text{carrier\_pickup}} - t_{\text{order\_approval}} \quad [56.7 \text{ hrs / } 24.8\%]$$
  $$T_{\text{transit}} = t_{\text{customer\_delivery}} - t_{\text{carrier\_pickup}} \quad [171.2 \text{ hrs / } 75.2\%]$$
* **Data Source:** `fct_orders`, `fct_shipments_deliveries`.
* **Data Provenance:** **Observed Public Data** (Olist dataset).
* **Business Interpretation:** Isolates the true root-cause bottleneck of delivery latency, demonstrating that 75.2% of customer wait time occurs while in carrier transit rather than merchant packing.
* **Target Benchmark:** Total fulfillment $\le 5$ calendar days. ThreadIQ baseline: **12.5 days average**.
* **Known Limitations:** Seller dispatch timestamp is proxied by carrier pickup scan in public logistics datasets.

---

### 3.3 Apparel Item Return Rate (`item_return_rate`)
* **Definition:** The proportion of fulfilled fashion apparel order lines that are returned by the customer post-delivery.
* **Mathematical Formula:**
  $$IRR = \left( \frac{\text{Order Items with } \text{is\_returned} = 1}{\text{Total Shipped Order Items}} \right) \times 100$$
* **Numerator:** Count of `fct_order_items` flagged with `is_returned = 1`.
* **Denominator:** Total count of shipped `fct_order_items`.
* **Data Source:** `fct_order_items`.
* **Data Provenance:** **Reconciled Data** (Observed Olist item sales merged with a synthetic fashion return taxonomy).
* **Business Interpretation:** Primary drain on net merchandise margin. Fashion returns cost substantial shipping, restocking, inspection, and inventory depreciation expenses.
* **Target Benchmark:** Apparel benchmark: $20.0\% - 25.0\%$. ThreadIQ baseline: **23.21%** ($938.99 refund exposure across sample).
* **Known Limitations:** In physical commerce, return processing can lag purchase dates by 14–30 days; trailing 30-day metrics reflect cohort maturity lag.

---

### 3.4 Return Reason Distribution (`return_reason_distribution`)
* **Definition:** The proportional breakdown of customer-reported root causes for apparel returns.
* **Mathematical Formulation:**
  $$\text{Share}_r = \left( \frac{\text{Returned Items with Reason } r}{\text{Total Returned Items}} \right) \times 100$$
* **Categories Evaluated:**
  * `SIZE_FIT`: Size too large, size too small, unflattering cut (**38.46% of returns**).
  * `QUALITY`: Defective stitching, fabric pilling, color mismatch (**23.08%**).
  * `STYLE`: Did not match website aesthetic (**19.23%**).
  * `WRONG_ITEM`: Warehouse picking error (**11.54%**).
  * `LATE_DELIVERY`: Arrived after event date (**7.69%**).
* **Data Source:** `fct_order_items.return_reason`.
* **Data Provenance:** **Synthetic Data** (calibrated against fashion e-commerce return benchmarks).
* **Business Interpretation:** Unambiguously identifies that **38.46% of returns are driven by sizing ambiguity**, establishing the direct product justification for PRD 01 (Digital Fit & Sizing Intelligence Engine).
* **Known Limitations:** Customer self-reported return reasons can suffer from bias (e.g., reporting "defective" to secure free return shipping).
