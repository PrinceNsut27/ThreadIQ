# ThreadIQ — Data Dictionary & Source-to-Target Mapping

## 1. Raw Dataset Inventory

### A. Olist Brazilian E-Commerce Dataset
- **Source:** Kaggle (`olistbr/brazilian-ecommerce`)
- **License:** CC BY-NC-SA 4.0 (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International)
- **Time Window:** 2016 – 2018
- **Files & Verified Schema:**

| File Name | Record Count | Primary Key | Foreign Keys | Key Attributes & Data Types | Missing Value Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `olist_customers_dataset.csv` | 99,441 | `customer_id` | — | `customer_id` (str), `customer_unique_id` (str), `customer_zip_code_prefix` (int), `customer_city` (str), `customer_state` (str) | 0 missing values |
| `olist_orders_dataset.csv` | 99,441 | `order_id` | `customer_id` | `order_id` (str), `customer_id` (str), `order_status` (str), `order_purchase_timestamp` (datetime), `order_approved_at` (datetime), `order_delivered_carrier_date` (datetime), `order_delivered_customer_date` (datetime), `order_estimated_delivery_date` (datetime) | `order_approved_at`: 160 nulls; `order_delivered_carrier_date`: 1,783 nulls; `order_delivered_customer_date`: 2,965 nulls (indicates non-delivered, canceled, or in-transit orders) |
| `olist_order_items_dataset.csv` | 112,650 | (`order_id`, `order_item_id`) | `order_id`, `product_id`, `seller_id` | `order_id` (str), `order_item_id` (int), `product_id` (str), `seller_id` (str), `shipping_limit_date` (datetime), `price` (float), `freight_value` (float) | 0 missing values |
| `olist_order_payments_dataset.csv` | 103,886 | (`order_id`, `payment_sequential`) | `order_id` | `order_id` (str), `payment_sequential` (int), `payment_type` (str), `payment_installments` (int), `payment_value` (float) | 0 missing values |
| `olist_order_reviews_dataset.csv` | 99,224 | `review_id` | `order_id` | `review_id` (str), `order_id` (str), `review_score` (int, 1-5), `review_comment_title` (str), `review_comment_message` (str), `review_creation_date` (datetime), `review_answer_timestamp` (datetime) | `review_comment_title`: ~88% missing; `review_comment_message`: ~58% missing |
| `olist_products_dataset.csv` | 32,951 | `product_id` | — | `product_id` (str), `product_category_name` (str), `product_name_lenght` (float), `product_description_lenght` (float), `product_photos_qty` (float), `product_weight_g` (float), `product_length_cm` (float), `product_height_cm` (float), `product_width_cm` (float) | `product_category_name`: 610 nulls; dimensional fields: 2 nulls |
| `olist_sellers_dataset.csv` | 3,095 | `seller_id` | — | `seller_id` (str), `seller_zip_code_prefix` (int), `seller_city` (str), `seller_state` (str) | 0 missing values |
| `olist_geolocation_dataset.csv` | 1,000,163 | Composite / Geo-lookup | — | `geolocation_zip_code_prefix` (int), `geolocation_lat` (float), `geolocation_lng` (float), `geolocation_city` (str), `geolocation_state` (str) | Multiple coordinate points per zip code |
| `product_category_name_translation.csv` | 71 | `product_category_name` | — | `product_category_name` (str), `product_category_name_english` (str) | Translation mapping table |

---

### B. Fashion Product Images Dataset
- **Source:** Kaggle (`paramaggarwal/fashion-product-images-dataset`)
- **License:** MIT License (Permissive)
- **Files & Verified Schema:**

| File Name | Record Count | Primary Key | Key Attributes & Data Types | Missing Value Notes |
| :--- | :--- | :--- | :--- | :--- |
| `styles.csv` | ~44,424 | `id` | `id` (int), `gender` (str), `masterCategory` (str), `subCategory` (str), `articleType` (str), `baseColour` (str), `season` (str), `year` (float), `usage` (str), `productDisplayName` (str) | Occasional unquoted commas in product titles causing parsing leaks; missing entries in `season`, `year`, and `usage`. |

---

## 2. Source-to-Target Mapping (Canonical Schema)

ThreadIQ maps raw observed entities and synthetic extensions into a clean relational SQLite schema (`threadiq.db`).

### Table: `dim_customers`
| Target Column | Target Data Type | Source Table & Column | Provenance | Transform / Business Logic |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | TEXT PK | `olist_customers.customer_id` | Observed (Olist) | Direct map |
| `customer_unique_id` | TEXT | `olist_customers.customer_unique_id` | Observed (Olist) | Direct map (identifies repeat purchasers) |
| `zip_code_prefix` | TEXT | `olist_customers.customer_zip_code_prefix` | Observed (Olist) | Zero-padded 5-digit string |
| `city` | TEXT | `olist_customers.customer_city` | Observed (Olist) | Title-cased |
| `state` | TEXT | `olist_customers.customer_state` | Observed (Olist) | Uppercase 2-letter state code |
| `customer_cohort` | TEXT | Derived | Observed (Olist) | Cohort based on month of first order (`YYYY-MM`) |
| `data_source` | TEXT | Literal `'olist'` | System | Provenance tracking |

### Table: `dim_products`
| Target Column | Target Data Type | Source Table & Column | Provenance | Transform / Business Logic |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | TEXT PK | Harmonized Key | Reconciled | Reconciled identifier linking fashion attributes to order items |
| `fashion_style_id` | TEXT | `styles.id` | Observed (Fashion) | Identifier from Kaggle fashion dataset |
| `master_category` | TEXT | `styles.masterCategory` | Observed (Fashion) | e.g. Apparel, Footwear, Accessories |
| `sub_category` | TEXT | `styles.subCategory` | Observed (Fashion) | e.g. Topwear, Bottomwear, Shoes |
| `article_type` | TEXT | `styles.articleType` | Observed (Fashion) | e.g. T-Shirts, Shirts, Casual Shoes |
| `base_colour` | TEXT | `styles.baseColour` | Observed (Fashion) | Standardized color string |
| `season` | TEXT | `styles.season` | Observed (Fashion) | e.g. Summer, Fall, Winter, Spring |
| `release_year` | INTEGER | `styles.year` | Observed (Fashion) | Cast to integer; null handled |
| `usage` | TEXT | `styles.usage` | Observed (Fashion) | e.g. Casual, Formal, Sports, Ethnic |
| `product_display_name` | TEXT | `styles.productDisplayName` | Observed (Fashion) | Cleaned title |
| `price_reference` | REAL | Harmonized / `order_items.price` | Reconciled | Median observed price or catalog reference |
| `catalog_completeness_score` | INTEGER | Derived | Derived | Percentage (0–100) of mandatory attributes populated |
| `data_source` | TEXT | Literal `'reconciled'` | System | Provenance tracking |

### Table: `fct_orders`
| Target Column | Target Data Type | Source Table & Column | Provenance | Transform / Business Logic |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | TEXT PK | `olist_orders.order_id` | Observed (Olist) | Direct map |
| `customer_id` | TEXT FK | `olist_orders.customer_id` | Observed (Olist) | References `dim_customers.customer_id` |
| `order_status` | TEXT | `olist_orders.order_status` | Observed (Olist) | Status (delivered, shipped, canceled, etc.) |
| `purchase_timestamp` | TIMESTAMP | `olist_orders.order_purchase_timestamp` | Observed (Olist) | ISO-8601 UTC timestamp |
| `approved_at` | TIMESTAMP | `olist_orders.order_approved_at` | Observed (Olist) | ISO-8601 UTC timestamp |
| `estimated_delivery_date` | TIMESTAMP | `olist_orders.order_estimated_delivery_date` | Observed (Olist) | ISO-8601 UTC timestamp |
| `data_source` | TEXT | Literal `'olist'` | System | Provenance tracking |

### Table: `fct_order_items`
| Target Column | Target Data Type | Source Table & Column | Provenance | Transform / Business Logic |
| :--- | :--- | :--- | :--- | :--- |
| `order_item_uid` | TEXT PK | Derived | Reconciled | Composite unique key: `{order_id}_{order_item_id}` |
| `order_id` | TEXT FK | `olist_order_items.order_id` | Observed (Olist) | References `fct_orders.order_id` |
| `order_item_id` | INTEGER | `olist_order_items.order_item_id` | Observed (Olist) | Item sequence index within order |
| `product_id` | TEXT FK | Harmonized / `olist_order_items.product_id` | Reconciled | References `dim_products.product_id` |
| `seller_id` | TEXT FK | `olist_order_items.seller_id` | Observed (Olist) | References `dim_sellers.seller_id` |
| `shipping_limit_date` | TIMESTAMP | `olist_order_items.shipping_limit_date` | Observed (Olist) | SLA deadline for seller dispatch |
| `price` | REAL | `olist_order_items.price` | Observed (Olist) | Item selling price |
| `freight_value` | REAL | `olist_order_items.freight_value` | Observed (Olist) | Shipping charge |
| `return_reason_code` | TEXT | Synthetic / Derived | Synthetic | Fashion return reason for canceled/low-review orders (`SIZE_FIT`, etc.) |
| `data_source` | TEXT | Literal `'olist'` | System | Provenance tracking |

### Table: `fct_shipments_deliveries`
| Target Column | Target Data Type | Source Table & Column | Provenance | Transform / Business Logic |
| :--- | :--- | :--- | :--- | :--- |
| `shipment_id` | TEXT PK | Derived | Reconciled | `{order_id}_{seller_id}` |
| `order_id` | TEXT FK | `olist_orders.order_id` | Observed (Olist) | References `fct_orders.order_id` |
| `seller_id` | TEXT FK | `olist_order_items.seller_id` | Observed (Olist) | References `dim_sellers.seller_id` |
| `dispatched_at` | TIMESTAMP | `olist_orders.order_delivered_carrier_date` | Observed (Olist) | Carrier pickup timestamp |
| `delivered_customer_date`| TIMESTAMP | `olist_orders.order_delivered_customer_date`| Observed (Olist) | Customer delivery timestamp |
| `estimated_delivery_date`| TIMESTAMP | `olist_orders.order_estimated_delivery_date`| Observed (Olist) | Promised delivery window |
| `order_to_dispatch_hours`| INTEGER | Derived | Derived | `(dispatched_at - purchase_timestamp)` in hours |
| `dispatch_to_delivery_hours`| INTEGER | Derived | Derived | `(delivered_customer_date - dispatched_at)` in hours |
| `is_late` | INTEGER | Derived | Derived | `1` if `delivered_customer_date > estimated_delivery_date`, else `0` |
| `data_source` | TEXT | Literal `'olist'` | System | Provenance tracking |

### Synthetic Tables (Strictly Provenanced)

#### `fct_sessions`
- `session_id` (TEXT PK) — Unique browsing session ID
- `customer_id` (TEXT FK $\rightarrow$ `dim_customers.customer_id`) — User ID
- `session_start` (TIMESTAMP) — Session start time
- `session_end` (TIMESTAMP) — Session termination time
- `device_type` (TEXT) — `mobile`, `desktop`, or `tablet`
- `traffic_source` (TEXT) — `organic_search`, `direct`, `paid_social`, `affiliate`
- `converted_flag` (INTEGER) — `1` if session resulted in purchase, else `0`
- `source_type` (TEXT) — `'synthetic'`
- `data_source` (TEXT) — `'synthetic'`

#### `fct_events_clickstream`
- `event_id` (TEXT PK) — Unique event identifier (`ev_{session_id}_{step:02d}`)
- `session_id` (TEXT FK $\rightarrow$ `fct_sessions.session_id`) — Session reference
- `customer_id` (TEXT FK $\rightarrow$ `dim_customers.customer_id`) — User reference
- `event_timestamp` (TIMESTAMP) — Event occurrence time
- `event_type` (TEXT) — Stage: `homepage_impression`, `search_query`, `category_page_view`, `product_detail_view`, `add_to_wishlist`, `add_to_cart`, `remove_from_cart`, `checkout_started`, `payment_attempted`, `purchase_completed`
- `product_id` (TEXT FK $\rightarrow$ `dim_products.product_id`, nullable) — Product reference
- `category` (TEXT, nullable) — Garment / product category
- `search_query` (TEXT, nullable) — Query string for search events
- `device_type` (TEXT) — `mobile`, `desktop`, `tablet`
- `traffic_source` (TEXT) — Acquisition channel
- `price_at_event` (REAL, nullable) — Active unit price at time of view/cart
- `source_type` (TEXT) — `'synthetic'`
- `data_source` (TEXT) — `'synthetic'`

#### `fct_search_queries`
- `query_id` (TEXT PK) — Search query event ID
- `session_id` (TEXT FK $\rightarrow$ `fct_sessions.session_id`) — Session reference
- `customer_id` (TEXT) — Customer reference
- `query_timestamp` (TIMESTAMP) — Query time
- `search_term` (TEXT) — Submitted search string
- `result_count` (INTEGER) — Matching product count returned
- `zero_result_flag` (INTEGER) — `1` if 0 items found, else `0`
- `clicked_product_id` (TEXT FK $\rightarrow$ `dim_products.product_id`, nullable) — Clicked product SKU
- `source_type` (TEXT) — `'synthetic'`
- `data_source` (TEXT) — `'synthetic'`

#### `fct_inventory_snapshots`
- `snapshot_id` (TEXT PK) — `{product_id}_{snapshot_date}`
- `product_id` (TEXT FK $\rightarrow$ `dim_products.product_id`) — Product reference
- `snapshot_date` (DATE) — Daily snapshot calendar date
- `stock_on_hand` (INTEGER) — Physical units in warehouse
- `reserved_quantity` (INTEGER) — Units locked in active checkout sessions
- `available_quantity` (INTEGER) — `stock_on_hand - reserved_quantity`
- `warehouse_id` (TEXT) — Simulated warehouse identifier (`WH_NORTH_01`, `WH_SOUTH_02`, `WH_CENTRAL_01`)
- `replenishment_quantity` (INTEGER) — Units added on restock events
- `historical_daily_velocity` (REAL) — 14-day trailing daily sales velocity
- `days_of_cover` (REAL) — `available_quantity / velocity`
- `stockout_flag` (INTEGER) — `1` if `available_quantity == 0`, else `0`
- `replenishment_recommendation` (TEXT) — `CRITICAL_REPLENISHMENT`, `HEALTHY`, `EXCESS_STOCK`
- `source_type` (TEXT) — `'synthetic'`
- `data_source` (TEXT) — `'synthetic'`

#### `fct_promotions`
- `promotion_id` (TEXT PK) — Unique promotion ID
- `product_id` (TEXT FK $\rightarrow$ `dim_products.product_id`, nullable) — Discounted product SKU
- `category` (TEXT, nullable) — Discounted merchandise category
- `discount_percentage` (REAL) — Promotional markdown (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)
- `start_date` (DATE) — Campaign launch date
- `end_date` (DATE) — Campaign expiration date
- `promotion_type` (TEXT) — `SEASONAL_CLEARANCE`, `FLASH_SALE`, `CATEGORY_DISCOUNT`, `NEW_CUSTOMER_VOUCHER`
- `source_type` (TEXT) — `'synthetic'`
- `data_source` (TEXT) — `'synthetic'`
