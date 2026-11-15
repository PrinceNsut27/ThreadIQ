# ThreadIQ — Product Metrics Dictionary

This document serves as the enterprise standard metric catalog for ThreadIQ across Storefront, Inbound Supply Chain, and Outbound Supply Chain & Logistics.

---

## 1. Storefront Product Analytics Metrics

### 1.1 Stage Conversion Rate (`stage_conversion_rate`)
- **Product Area**: Storefront — Conversion Funnel
- **Definition**: The percentage of digital shopping sessions that successfully progress from the previous funnel milestone to the current funnel milestone.
- **Business Purpose**: Isolates specific user journey transitions experiencing friction (e.g., PDP-to-cart drop-off vs cart-to-checkout drop-off).
- **Formula**:
  $$CR_i = \left( \frac{\text{Sessions reaching Stage } i}{\text{Sessions reaching Stage } i-1} \right) \times 100$$
- **Numerator**: Distinct count of `session_id` reaching stage $i$.
- **Denominator**: Distinct count of `session_id` reaching stage $i-1$.
- **Dimensions**: Device type (`mobile`, `desktop`), traffic source (`organic_search`, `paid_social`, `direct`), date/hour.
- **Time Horizon**: Daily, Weekly, Trailing 30 Days.
- **Target SLA / Benchmark**: PDP-to-Cart $\ge 15\%$; Cart-to-Checkout $\ge 50\%$; Checkout-to-Purchase $\ge 70\%$.
- **Data Lineage**: Synthetic (`fct_sessions`, `fct_events`).

---

### 1.2 Cumulative Conversion Rate (`cumulative_conversion_rate`)
- **Product Area**: Storefront — Conversion Funnel
- **Definition**: The proportion of all starting shopping sessions that reach a given funnel step relative to the top of the funnel (Homepage Impression).
- **Business Purpose**: Overall end-to-end efficiency measurement of the digital commerce storefront.
- **Formula**:
  $$CR_{\text{cum}, i} = \left( \frac{\text{Sessions reaching Stage } i}{\text{Total Initial Sessions (Stage 1)}} \right) \times 100$$
- **Numerator**: Distinct count of `session_id` active at stage $i$.
- **Denominator**: Distinct count of `session_id` recorded at Stage 1 (`homepage_impression`).
- **Dimensions**: Device type, marketing campaign channel, customer cohort.
- **Time Horizon**: Daily, Weekly, Monthly.
- **Target SLA / Benchmark**: End-to-end purchase completion $\ge 2.5\% - 3.5\%$ (fashion benchmark).
- **Data Lineage**: Synthetic (`fct_sessions`, `fct_events`).

---

### 1.3 Cart Abandonment Rate (`cart_abandonment_rate`)
- **Product Area**: Storefront — Shopping Bag Optimization
- **Definition**: The percentage of shopping sessions in which at least one item was added to the cart, but no final order was completed.
- **Business Purpose**: Quantifies unrecovered commercial intent and potential checkout friction.
- **Formula**:
  $$CAR = \left( \frac{\text{Sessions}_{\text{add\_to\_cart}} - \text{Sessions}_{\text{purchase}}}{\text{Sessions}_{\text{add\_to\_cart}}} \right) \times 100$$
- **Numerator**: Count of sessions with `add_to_cart` event minus sessions with `purchase_completed` event.
- **Denominator**: Total count of sessions with at least one `add_to_cart` event.
- **Dimensions**: Device type, total cart value tier, traffic acquisition source.
- **Time Horizon**: Daily, Weekly rolling.
- **Target SLA / Benchmark**: $< 70.0\%$ (Industry fashion average is ~70-75%).
- **Data Lineage**: Synthetic (`fct_events`).

---

### 1.4 Search Click-Through Rate (`search_click_through_rate`)
- **Product Area**: Storefront — Search & Discovery
- **Definition**: The percentage of user search queries that result in at least one product detail page view.
- **Business Purpose**: Measures search relevance, ranking precision, and query-to-catalog match quality.
- **Formula**:
  $$CTR_{\text{search}} = \left( \frac{\text{Search Queries with } \ge 1 \text{ Clicked Product}}{\text{Total Search Queries Executed}} \right) \times 100$$
- **Numerator**: Count of `fct_search_queries` records where `clicked_product_id IS NOT NULL`.
- **Denominator**: Total count of `fct_search_queries` records.
- **Dimensions**: Search term, category filter applied, user device.
- **Time Horizon**: Daily, Weekly.
- **Target SLA / Benchmark**: $\ge 35.0\%$.
- **Data Lineage**: Synthetic (`fct_search_queries`).

---

### 1.5 Zero-Result Search Rate (`zero_result_search_rate`)
- **Product Area**: Storefront — Search & Discovery
- **Definition**: The proportion of user-entered search queries that yielded zero matching products in the fashion catalog.
- **Business Purpose**: Uncovers unmet customer demand, missing catalog keywords, vocabulary mismatch, and catalog gaps.
- **Formula**:
  $$ZRSR = \left( \frac{\text{Search Queries with } \text{results\_count} = 0}{\text{Total Search Queries Executed}} \right) \times 100$$
- **Numerator**: Count of `fct_search_queries` records where `results_count = 0`.
- **Denominator**: Total count of `fct_search_queries` records.
- **Dimensions**: Raw search query string, normalized query tokens.
- **Time Horizon**: Trailing 7 Days, Trailing 30 Days.
- **Target SLA / Benchmark**: $< 10.0\%$.
- **Data Lineage**: Synthetic (`fct_search_queries`).

---

### 1.6 Product Purchase Conversion Rate (`product_purchase_conversion_rate`)
- **Product Area**: Storefront — Product Merchandising
- **Definition**: The proportion of sessions viewing a specific SKU that subsequently resulted in a purchase of that SKU.
- **Business Purpose**: Evaluates individual fashion product appeal, price-value perception, and merchandising effectiveness.
- **Formula**:
  $$CR_{\text{prod}, j} = \left( \frac{\text{Sessions Purchasing Product } j}{\text{Sessions Viewing Product } j} \right) \times 100$$
- **Numerator**: Distinct sessions where product $j$ was purchased.
- **Denominator**: Distinct sessions where product $j$ was viewed (`product_detail_view`).
- **Dimensions**: Product ID, Category, Sub-Category, Brand.
- **Time Horizon**: Monthly, Quarterly.
- **Target SLA / Benchmark**: $\ge 5.0\%$.
- **Data Lineage**: Reconciled (Synthetic `fct_events` + Observed `fct_order_items`).

---

### 1.7 Repeat Purchase Rate (`repeat_purchase_rate`)
- **Product Area**: Storefront — Customer Analytics & Retention
- **Definition**: The percentage of unique customers who have made two or more confirmed purchases over their lifetime.
- **Business Purpose**: Assesses customer loyalty, product satisfaction, and brand stickiness.
- **Formula**:
  $$RPR = \left( \frac{\text{Unique Customers with Lifetime Orders } \ge 2}{\text{Total Unique Customers with } \ge 1 \text{ Order}} \right) \times 100$$
- **Numerator**: Count of `customer_unique_id` with `COUNT(order_id) >= 2`.
- **Denominator**: Count of `customer_unique_id` with `COUNT(order_id) >= 1`.
- **Dimensions**: Acquisition cohort, geographic state, customer RFM segment.
- **Time Horizon**: Lifetime, Trailing 12 Months.
- **Target SLA / Benchmark**: $\ge 25.0\% - 30.0\%$.
- **Data Lineage**: Observed (`dim_customers`, `fct_orders`).

---

### 1.8 Average Order Value (`average_order_value`)
- **Product Area**: Storefront — Commercial Economics
- **Definition**: The average gross monetary value generated per completed customer transaction.
- **Business Purpose**: Core commercial metric used in unit economic models and promotional elasticity evaluations.
- **Formula**:
  $$\text{AOV} = \frac{\sum_{i=1}^{N_{\text{orders}}} \text{order\_value}_i}{N_{\text{orders}}}$$
- **Numerator**: Total sum of item price plus freight across valid orders.
- **Denominator**: Total count of completed, non-canceled orders.
- **Dimensions**: Customer segment, device type, promotional status.
- **Time Horizon**: Monthly, Quarterly.
- **Target SLA / Benchmark**: Sustainable margin target ($\ge \$100.00$).
- **Data Lineage**: Observed (`fct_orders`, `fct_order_items`).

---

## 2. Inbound Supply Chain Analytics Metrics

### 2.1 Catalog Completeness Score (`catalog_completeness_score`)
- **Product Area**: Inbound — Catalog Operations
- **Definition**: The percentage of mandatory merchandising attributes (`article_type`, `sub_category`, `base_colour`, `season`, `usage`) populated with non-null values.
- **Business Purpose**: Guarantees catalog data quality for discovery, search filtering, and faceted navigation.
- **Formula**:
  $$S_j = \left( \frac{\sum_{k=1}^5 \mathbb{I}(\text{attribute}_{j,k} \ne \text{null})}{5} \right) \times 100$$
- **Numerator**: Count of non-null mandatory fields for SKU $j$.
- **Denominator**: Total count of mandatory fields (5).
- **Dimensions**: Product ID, Category, Merchant / Supplier.
- **Time Horizon**: Real-time snapshot.
- **Target SLA / Benchmark**: $100.0\%$ (Zero missing attributes).
- **Data Lineage**: Reconciled (`dim_products` via Fashion Kaggle & Olist).

---

### 2.2 In-Stock Availability Rate (`in_stock_availability_rate`)
- **Product Area**: Inbound — Inventory Health
- **Definition**: The proportion of active SKU-days where physical inventory on hand was greater than zero.
- **Business Purpose**: Measures merchandise availability and operational fulfillment capability.
- **Formula**:
  $$ISAR = \left( 1 - \frac{\text{Total Out-of-Stock SKU Days}}{\text{Total Observed SKU Days}} \right) \times 100$$
- **Numerator**: Count of daily snapshot records where `available_quantity > 0`.
- **Denominator**: Total daily snapshot records across all active products.
- **Dimensions**: Master Category, Sub-Category, Supplier.
- **Time Horizon**: Daily, Trailing 30 Days, Trailing 90 Days.
- **Target SLA / Benchmark**: $\ge 98.0\%$.
- **Data Lineage**: Synthetic (`fct_inventory_snapshots`).

---

### 2.3 Stockout Rate (`stockout_rate`)
- **Product Area**: Inbound — Inventory Health
- **Definition**: The proportion of active SKU-days where inventory was zero, preventing storefront purchase.
- **Business Purpose**: Identifies lost sales opportunity and inventory replenishment delays.
- **Formula**:
  $$SOR = 100\% - ISAR = \left( \frac{\text{SKU Days with } \text{available\_quantity} = 0}{\text{Total Observed SKU Days}} \right) \times 100$$
- **Numerator**: Count of records where `available_quantity = 0`.
- **Denominator**: Total active SKU-days.
- **Dimensions**: SKU, Sub-Category, Supplier.
- **Time Horizon**: Trailing 30 Days.
- **Target SLA / Benchmark**: $\le 2.0\%$.
- **Data Lineage**: Synthetic (`fct_inventory_snapshots`).

---

### 2.4 Days of Cover (`days_of_cover`)
- **Product Area**: Inbound — Inventory Planning
- **Definition**: The estimated number of days current on-hand warehouse inventory will last based on historical sales velocity.
- **Business Purpose**: Governs inventory purchase orders, prevents stockouts, and flags capital over-investment.
- **Formula**:
  $$DoC_j = \frac{\text{Current Available Quantity}_j}{\max(\text{Sales Velocity}_j, 0.1)}$$
- **Numerator**: Current stock on hand in warehouse for SKU $j$.
- **Denominator**: 30-day average daily unit sales velocity ($V_j$).
- **Dimensions**: SKU, Category, Warehouse Location.
- **Time Horizon**: Real-time evaluation based on trailing 30-day sales.
- **Target SLA / Benchmark**: 14 to 45 Days (Fast-fashion optimal window).
- **Data Lineage**: Reconciled (Synthetic `fct_inventory_snapshots` + Observed `fct_order_items`).

---

### 2.5 Average Promotional Discount Depth (`avg_discount_depth`)
- **Product Area**: Inbound — Pricing & Commercial Strategy
- **Definition**: The average percentage markdown applied across all active or historical promotional campaigns.
- **Business Purpose**: Protects gross margins and prevents excessive promotional brand erosion.
- **Formula**:
  $$\overline{\text{Discount}} = \frac{1}{K} \sum_{k=1}^K \text{discount\_percent}_k$$
- **Numerator**: Sum of nominal discount percentage points across campaigns.
- **Denominator**: Total active promotional campaigns ($K$).
- **Dimensions**: Promotion Type (`FLASH_SALE`, `SEASONAL_CLEARANCE`, `CATEGORY_DISCOUNT`), Category.
- **Time Horizon**: Active campaign window, Quarterly.
- **Target SLA / Benchmark**: Balanced mix: Flash Sales $\le 30\%$, Seasonal Clearance $\le 40\%$.
- **Data Lineage**: Synthetic (`fct_promotions`).

---

## 3. Outbound Supply Chain & Logistics Metrics

### 3.1 On-Time Delivery Rate (`on_time_delivery_rate` / `OTD%`)
- **Product Area**: Outbound — Logistics & Fulfillment SLA
- **Definition**: The percentage of completed customer shipments delivered on or before the estimated delivery promise date provided at checkout.
- **Business Purpose**: Core logistics SLA measuring carrier reliability and customer delivery satisfaction.
- **Formula**:
  $$OTD\% = \left( \frac{\text{Orders with } t_{\text{actual\_delivery}} \le t_{\text{estimated\_delivery}}}{\text{Total Delivered Orders}} \right) \times 100$$
- **Numerator**: Count of delivered shipments where `actual_delivery_timestamp <= estimated_delivery_timestamp`.
- **Denominator**: Total count of orders with confirmed customer delivery.
- **Dimensions**: Destination State (`customer_state`), Logistics Carrier, Shipping Tier.
- **Time Horizon**: Weekly, Monthly.
- **Target SLA / Benchmark**: $\ge 95.0\%$.
- **Data Lineage**: Observed (`fct_shipments_deliveries`, `fct_orders`).

---

### 3.2 Late Delivery Rate (`late_delivery_rate`)
- **Product Area**: Outbound — Logistics SLA
- **Definition**: The percentage of completed shipments that breached the delivery promise date.
- **Business Purpose**: Drives proactive customer service notifications, carrier penalty claims, and concession budget sizing.
- **Formula**:
  $$LDR\% = 100\% - OTD\% = \left( \frac{\text{Orders with } t_{\text{actual\_delivery}} > t_{\text{estimated\_delivery}}}{\text{Total Delivered Orders}} \right) \times 100$$
- **Numerator**: Count of orders delivered past the estimated date.
- **Denominator**: Total delivered orders.
- **Dimensions**: Destination State, Shipping Carrier.
- **Time Horizon**: Weekly, Monthly.
- **Target SLA / Benchmark**: $\le 5.0\%$.
- **Data Lineage**: Observed (`fct_shipments_deliveries`).

---

### 3.3 Average Delivery Duration (`average_delivery_time`)
- **Product Area**: Outbound — Logistics SLA
- **Definition**: The average number of calendar days elapsed between initial customer purchase and final physical doorstep delivery.
- **Business Purpose**: Benchmarks overall supply chain transit speed against competitive market expectations.
- **Formula**:
  $$\bar{T}_{\text{delivery}} = \frac{1}{N_{\text{del}}} \sum_{i=1}^{N_{\text{del}}} (t_{\text{actual\_delivery}, i} - t_{\text{purchase}, i}) \quad \text{[days]}$$
- **Numerator**: Total cumulative calendar days across delivered orders.
- **Denominator**: Count of confirmed delivered orders ($N_{\text{del}}$).
- **Dimensions**: Origin Seller State, Destination Customer State, Shipping Carrier.
- **Time Horizon**: Monthly.
- **Target SLA / Benchmark**: $\le 5.0 \text{ calendar days}$.
- **Data Lineage**: Observed (`fct_orders`, `fct_shipments_deliveries`).

---

### 3.4 Order Cancellation Rate (`order_cancellation_rate`)
- **Product Area**: Outbound — Order Operations
- **Definition**: The proportion of all placed customer orders that are canceled prior to final fulfillment.
- **Business Purpose**: Monitors lost gross revenue, stock reservation lockup, and pre-fulfillment dissatisfaction.
- **Formula**:
  $$OCR = \left( \frac{\text{Orders with Status } = \text{'canceled'}}{\text{Total Orders Placed}} \right) \times 100$$
- **Numerator**: Count of `fct_orders` records with `order_status = 'canceled'`.
- **Denominator**: Total count of all recorded `fct_orders`.
- **Dimensions**: Cancellation stage (pre-dispatch vs in-transit), customer segment, payment type.
- **Time Horizon**: Daily, Weekly, Monthly.
- **Target SLA / Benchmark**: $\le 3.0\%$.
- **Data Lineage**: Observed (`fct_orders`).

---

### 3.5 Item Return Rate (`item_return_rate`)
- **Product Area**: Outbound — Reverse Logistics
- **Definition**: The percentage of shipped fashion apparel items that are physically returned by consumers.
- **Business Purpose**: Quantifies gross-to-net sales degradation, reverse logistics expenses, and inventory inspection costs.
- **Formula**:
  $$IRR = \left( \frac{\text{Order Items with } \text{is_returned} = \text{True}}{\text{Total Shipped Order Items}} \right) \times 100$$
- **Numerator**: Count of `fct_order_items` records flagged with `is_returned = 1`.
- **Denominator**: Total count of shipped `fct_order_items`.
- **Dimensions**: Return Reason, Product Sub-Category, Size / Fit Profile.
- **Time Horizon**: Monthly, Quarterly.
- **Target SLA / Benchmark**: Apparel industry benchmark is 20-25%; operational target $\le 18.0\%$.
- **Data Lineage**: Reconciled (Observed `fct_order_items` + Synthetic Return Taxonomy).

---

### 3.6 Merchant Dispatch SLA Compliance (`slow_dispatch_rate`)
- **Product Area**: Outbound — Merchant Warehouse Operations
- **Definition**: The proportion of merchant order lines where the duration between order payment confirmation and carrier handover exceeded the 48-hour fulfillment SLA.
- **Business Purpose**: Enforces merchant compliance, identifies slow-packing vendors, and prevents carrier pickup delays.
- **Formula**:
  $$SDR_s = \left( \frac{\text{Orders where } (t_{\text{carrier\_pickup}} - t_{\text{order\_approval}}) > 48\text{ hrs}}{\text{Total Orders Fulfilled by Seller } s} \right) \times 100$$
- **Numerator**: Orders fulfilled by seller $s$ exceeding 48 hours to carrier handover.
- **Denominator**: Total orders fulfilled by seller $s$.
- **Dimensions**: Seller ID, Seller State, Product Category.
- **Time Horizon**: Monthly rolling.
- **Target SLA / Benchmark**: $\le 10.0\%$.
- **Data Lineage**: Observed (`fct_orders`, `fct_shipments_deliveries`, `dim_sellers`).
