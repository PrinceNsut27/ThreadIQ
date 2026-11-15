# ThreadIQ — Database Schema Specification

This document specifies the relational database schema implemented in SQLite (`data/threadiq.db`) using SQLAlchemy Core metadata (`src/threadiq/data/loaders.py`).

---

## 1. Relational Entity Schema

### Dimension Tables

#### `dim_customers`
Stores customer identity, geographic attributes, and cohort assignments.
- **`customer_id`** (`VARCHAR(64)`, Primary Key) — Unique customer order identifier.
- **`customer_unique_id`** (`VARCHAR(64)`, Indexed, NOT NULL) — Identifies unique individuals for repeat purchaser tracking.
- **`zip_code_prefix`** (`VARCHAR(10)`) — 5-digit zero-padded postal code prefix.
- **`city`** (`VARCHAR(100)`) — Customer city name (Title Cased).
- **`state`** (`VARCHAR(10)`, Indexed) — 2-letter state code (e.g., `SP`, `RJ`).
- **`customer_cohort`** (`VARCHAR(10)`, Indexed) — Month of first recorded purchase (`YYYY-MM`).
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'olist'`).

#### `dim_sellers`
Stores merchant supplier profiles and warehouse locations.
- **`seller_id`** (`VARCHAR(64)`, Primary Key) — Unique seller identifier.
- **`zip_code_prefix`** (`VARCHAR(10)`) — 5-digit zero-padded postal code prefix.
- **`city`** (`VARCHAR(100)`) — Seller municipality (Title Cased).
- **`state`** (`VARCHAR(10)`, Indexed) — 2-letter state code.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'olist'`).

#### `dim_products`
Unified merchandise catalog integrating fashion attributes and catalog completeness scoring.
- **`product_id`** (`VARCHAR(64)`, Primary Key) — Unique product SKU identifier.
- **`fashion_style_id`** (`VARCHAR(64)`, Indexed) — Style ID from Kaggle Fashion Product Images.
- **`master_category`** (`VARCHAR(64)`, Indexed) — High-level category (e.g., `Apparel`, `Footwear`).
- **`sub_category`** (`VARCHAR(64)`, Indexed) — Category grouping (e.g., `Topwear`, `Bottomwear`, `Shoes`).
- **`article_type`** (`VARCHAR(64)`, Indexed) — Granular merchandise type (e.g., `T-Shirts`, `Jeans`).
- **`base_colour`** (`VARCHAR(64)`) — Primary garment/item color.
- **`season`** (`VARCHAR(32)`) — Fashion season (`Summer`, `Fall`, `Winter`, `Spring`, `All`).
- **`release_year`** (`INTEGER`) — Product launch year.
- **`usage`** (`VARCHAR(64)`) — Occasion of use (`Casual`, `Ethnic`, `Formal`, `Sports`).
- **`product_display_name`** (`TEXT`) — Complete commercial title displayed on the storefront.
- **`price_reference`** (`REAL`) — Benchmark/median catalog price.
- **`catalog_completeness_score`** (`INTEGER`) — Automated score (0–100) assessing attribute richness.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'fashion_kaggle'` or `'olist'`).

---

### Fact Tables

#### `fct_orders`
Tracks the lifecycle timestamps and statuses of orders.
- **`order_id`** (`VARCHAR(64)`, Primary Key) — Unique order identifier.
- **`customer_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `dim_customers.customer_id`, Indexed, NOT NULL).
- **`order_status`** (`VARCHAR(32)`, Indexed) — Normalized order status (`delivered`, `shipped`, `canceled`, etc.).
- **`purchase_timestamp`** (`TIMESTAMP`, Indexed) — Order placement time (UTC).
- **`approved_at`** (`TIMESTAMP`) — Payment authorization timestamp.
- **`estimated_delivery_date`** (`TIMESTAMP`) — Promised delivery window promised at checkout.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'olist'`).

#### `fct_order_items`
Item-level order details, pricing, seller routing, and fashion return attributions.
- **`order_item_uid`** (`VARCHAR(128)`, Primary Key) — Composite key: `{order_id}_{order_item_id}`.
- **`order_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `fct_orders.order_id`, Indexed, NOT NULL).
- **`order_item_id`** (`INTEGER`, NOT NULL) — Item index within order.
- **`product_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `dim_products.product_id`, Indexed, NOT NULL).
- **`seller_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `dim_sellers.seller_id`, Indexed, NOT NULL).
- **`shipping_limit_date`** (`TIMESTAMP`) — Deadline for seller handover to carrier.
- **`price`** (`REAL`, NOT NULL) — Unit selling price (strictly $\ge 0.0$).
- **`freight_value`** (`REAL`, NOT NULL) — Freight cost component (strictly $\ge 0.0$).
- **`return_reason_code`** (`VARCHAR(64)`, Indexed) — Fashion return reason (`SIZE_FIT`, `QUALITY_FABRIC`, etc.).
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'olist'`).

#### `fct_order_payments`
Multi-installment payment transactions per order.
- **`payment_uid`** (`VARCHAR(128)`, Primary Key) — Composite key: `{order_id}_{payment_sequential}`.
- **`order_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `fct_orders.order_id`, Indexed, NOT NULL).
- **`payment_sequential`** (`INTEGER`, NOT NULL) — Payment split sequence.
- **`payment_type`** (`VARCHAR(32)`, Indexed) — Payment method (`credit_card`, `boleto`, `voucher`, etc.).
- **`payment_installments`** (`INTEGER`) — Selected installment count.
- **`payment_value`** (`REAL`, NOT NULL) — Monetary transaction amount.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'olist'`).

#### `fct_order_reviews`
Customer survey ratings and satisfaction feedback.
- **`review_id`** (`VARCHAR(64)`, Primary Key) — Unique review survey ID.
- **`order_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `fct_orders.order_id`, Indexed, NOT NULL).
- **`review_score`** (`INTEGER`, Indexed, NOT NULL) — Customer rating integer from 1 to 5.
- **`review_comment_title`** (`TEXT`) — Survey comment headline.
- **`review_comment_message`** (`TEXT`) — Survey review message body.
- **`review_creation_date`** (`TIMESTAMP`) — Survey dispatch date.
- **`review_answer_timestamp`** (`TIMESTAMP`) — Response submission time.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'olist'`).

#### `fct_shipments_deliveries`
Fulfillment duration decomposition and logistics SLA metrics.
- **`shipment_id`** (`VARCHAR(128)`, Primary Key) — `{order_id}_shipment`.
- **`order_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `fct_orders.order_id`, Indexed, NOT NULL).
- **`seller_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `dim_sellers.seller_id`, Indexed, NOT NULL).
- **`dispatched_at`** (`TIMESTAMP`) — Carrier handover timestamp.
- **`delivered_customer_date`** (`TIMESTAMP`) — Actual delivery time.
- **`estimated_delivery_date`** (`TIMESTAMP`) — Promised delivery date.
- **`order_to_dispatch_hours`** (`INTEGER`) — Duration from purchase to carrier dispatch.
- **`dispatch_to_delivery_hours`** (`INTEGER`) — Duration from dispatch to delivery.
- **`delivery_delay_hours`** (`INTEGER`) — Delay beyond promise (positive indicates late).
- **`is_late`** (`INTEGER`, Indexed) — `1` if delivered past estimate, else `0`.
- **`is_canceled`** (`INTEGER`, Indexed) — `1` if order was canceled, else `0`.
- **`carrier_code`** (`VARCHAR(32)`) — Logistics carrier identifier.
- **`delivery_region`** (`VARCHAR(64)`) — Regional routing zone.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — Provenance flag (`'olist'`).

---

### Synthetic Simulation Tables (Clearly Provenanced)

#### `fct_sessions`
- **`session_id`** (`VARCHAR(64)`, Primary Key) — Unique browsing session ID.
- **`customer_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `dim_customers.customer_id`, Indexed, NOT NULL).
- **`session_start`** (`TIMESTAMP`, Indexed) — Session start timestamp.
- **`session_end`** (`TIMESTAMP`) — Session completion timestamp.
- **`device_type`** (`VARCHAR(32)`, Indexed) — `mobile`, `desktop`, or `tablet`.
- **`traffic_source`** (`VARCHAR(32)`, Indexed) — Acquisition channel (`organic_search`, `direct`, `paid_social`, `affiliate`).
- **`converted_flag`** (`INTEGER`, Indexed) — `1` if purchase occurred, else `0`.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — `'synthetic'`.

#### `fct_events_clickstream`
- **`event_id`** (`VARCHAR(64)`, Primary Key) — Unique clickstream event ID.
- **`session_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `fct_sessions.session_id`, Indexed, NOT NULL).
- **`customer_id`** (`VARCHAR(64)`, Indexed, NOT NULL).
- **`event_timestamp`** (`TIMESTAMP`, Indexed) — Event occurrence time.
- **`event_type`** (`VARCHAR(32)`, Indexed) — Stage: `impression`, `product_view`, `add_to_cart`, `checkout_start`, `purchase`.
- **`product_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `dim_products.product_id`, Indexed).
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — `'synthetic'`.

#### `fct_inventory_snapshots`
- **`snapshot_id`** (`VARCHAR(128)`, Primary Key) — `{product_id}_{snapshot_date}`.
- **`product_id`** (`VARCHAR(64)`, Foreign Key $\rightarrow$ `dim_products.product_id`, Indexed, NOT NULL).
- **`snapshot_date`** (`DATE`, Indexed) — Daily snapshot date.
- **`stock_on_hand`** (`INTEGER`, NOT NULL) — Physical warehouse inventory.
- **`reserved_stock`** (`INTEGER`, NOT NULL) — Stock locked in active checkouts/orders.
- **`available_stock`** (`INTEGER`, NOT NULL) — Unencumbered inventory available for sale.
- **`historical_daily_velocity`** (`REAL`) — 14-day trailing sales velocity (units/day).
- **`days_of_cover`** (`REAL`) — $\text{available\_stock} / \text{velocity}$.
- **`stockout_flag`** (`INTEGER`, Indexed) — `1` if available stock $\le 0$, else `0`.
- **`replenishment_recommendation`** (`VARCHAR(64)`) — `CRITICAL_REPLENISHMENT`, `HEALTHY`, or `EXCESS_STOCK`.
- **`data_source`** (`VARCHAR(32)`, NOT NULL) — `'synthetic'`.
