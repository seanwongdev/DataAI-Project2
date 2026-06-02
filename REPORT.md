# Module 2 Capstone Report
## Brazilian E-Commerce Data Pipeline & Analysis

---

## 1. Project Overview

This project builds an end-to-end data engineering pipeline on the Olist Brazilian E-Commerce dataset. Raw CSV data is ingested into BigQuery, transformed through a medallion architecture (Bronze → Silver → Gold) using dbt, validated with automated data quality tests, and analysed in Python notebooks to surface actionable business insights.

---

## 2. Dataset

**Source:** [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

9 CSV files covering orders, customers, products, sellers, order items, payments, reviews, geolocation, and product category translations. The dataset spans September 2016 to September 2018 with 112,650 order item records across 98,666 unique orders.

---

## 3. Architecture

```
CSV Files → Python (load.py) → BigQuery Bronze → dbt Staging → dbt Marts → Jupyter Notebooks
                                    (raw)           (silver)      (gold)       (analysis)
```

### Medallion Layers

| Layer | BigQuery Dataset | Populated By | Contents |
|---|---|---|---|
| Bronze | `bronze` | `ingestion/load.py` | Raw CSVs loaded as-is |
| Silver | `silver` | dbt staging models | Cleaned, typed, renamed |
| Gold | `gold` | dbt mart models | Star schema fact and dimension tables |

---

## 4. Tool Choices & Justifications

### Data Warehouse: BigQuery
**Chosen over:** DuckDB, PostgreSQL

BigQuery was selected for its serverless architecture, free tier (10GB storage, 1TB queries/month), and native integration with the Python `google-cloud-bigquery` client. Unlike DuckDB, BigQuery scales to petabyte-scale data without infrastructure management — appropriate for a pipeline that would run in production. Its column-oriented storage also makes aggregation queries significantly faster than row-oriented databases.

### Ingestion: Python + pandas
**Chosen over:** Meltano, Airbyte

The Olist dataset is a static one-time CSV load — Meltano and Airbyte are designed for recurring incremental extraction from live APIs and databases. Using a connector framework for a static file load would introduce unnecessary complexity. Python with pandas provides direct control over schema inference, error handling, and CSV cleaning (particularly important for the malformed reviews file which required pre-processing before BigQuery ingestion).

### Transformation: dbt
**Chosen over:** Raw SQL scripts, pandas

dbt provides three capabilities that raw SQL scripts cannot: automatic lineage tracking (which model depends on which), built-in test framework (unique, not_null, relationships, custom expressions), and auto-generated documentation. These are production-grade data engineering practices — a raw SQL script offers none of them. pandas was not used for transformations because keeping transformation logic in SQL within the warehouse avoids unnecessary data movement and is more performant at scale.

### Data Quality: dbt native tests + dbt_expectations
dbt native tests (`unique`, `not_null`, `relationships`, `accepted_values`) cover structural integrity. `dbt_expectations` extends this with statistical tests (value ranges, row count bounds) that catch data drift and business logic violations. Together, 55 tests were defined across all fact and dimension models.

### Analysis: Python + pandas + matplotlib
Standard, widely understood toolchain. BigQuery handles the heavy aggregation in SQL; pandas handles the final scoring logic (RFM quintiles) and charting. `google-cloud-bigquery` client returns query results directly as DataFrames, eliminating the need for SQLAlchemy or an intermediate ORM layer.

---

## 5. Star Schema Design

**Grain:** One row per order item — `(order_id, order_item_id)`

| Table | Source | Key columns |
|---|---|---|
| `fact_orders` | raw_order_items + raw_orders + raw_order_reviews | price, freight_value, total_amount, review_score |
| `dim_customer` | raw_customers | customer_id, city, state |
| `dim_product` | raw_products + category translation | product_id, category, dimensions |
| `dim_seller` | raw_sellers | seller_id, city, state |
| `dim_date` | derived from order_purchase_timestamp | year, month, quarter, day_of_week |

**Why star over snowflake:** Star schema denormalises dimensions for query simplicity and speed. With analytical workloads (aggregations, GROUP BY, joins), fewer joins means faster queries and simpler SQL — appropriate for a BI/reporting use case.

**Tables excluded:**
- `raw_order_payments` — multiple rows per order (installment/payment type splits) would break the grain
- `raw_geolocation` — city/state folded directly into dim_customer and dim_seller

---

## 6. Data Quality Issues Discovered & Resolved

### Issue 1 — Duplicate reviews in `raw_order_reviews`
**Discovery:** The `dbt_utils.unique_combination_of_columns` test on `fact_orders` failed with 658 violations, indicating the `(order_id, order_item_id)` grain was broken.

**Root cause:** `raw_order_reviews` contains multiple review records per `order_id` (a customer can submit more than one review per order). A naive `LEFT JOIN ON order_id` duplicated order item rows for every additional review.

**Resolution:** Introduced a CTE in `fact_orders.sql` using `ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_creation_date DESC)` to retain only the most recent review per order before joining. All 55 tests pass after this fix.

### Issue 2 — Missing English category translations
**Discovery:** `not_null` test on `dim_product.category` returned 623 warnings.

**Root cause:** 623 products (~1.9% of 33k) have Portuguese category names with no corresponding English translation in `product_category_name_translation.csv`.

**Resolution:** Accepted as a known data limitation. Nulls are preserved rather than filled with a placeholder (which would misrepresent the data). The test is configured as `severity: warn` so the pipeline does not fail — but the issue is flagged for visibility. In a production system, this would be escalated to the data owner for translation coverage.

---

## 7. Key Business Insights

### Monthly Sales Trend
- Revenue grew consistently from early 2017 through late 2018
- Peak month was **November 2017**, driven by Black Friday
- Revenue and order volume track closely — average order value is stable at ~R$140

**Recommendation:** Plan logistics and inventory capacity for Q4, with a pre-Black Friday campaign in October to capture early shoppers and smooth the fulfilment spike.

### Top Product Categories
- Revenue is concentrated — the top 3 categories account for a disproportionate share of total revenue
- **Health & Beauty**, **Watches & Gifts**, and **Bed/Bath/Table** are the dominant categories
- Long tail of categories each contribute <1% of revenue individually

**Recommendation:** Defend and grow seller base in top 3 categories. Target mid-tier categories with high order volume but low average order value for upselling improvement.

### RFM Customer Segmentation
- The majority of customers are one-time buyers (low frequency) — typical for marketplace businesses
- Champions and Loyal customers are a small % of the base but contribute disproportionately to revenue
- A significant At Risk and Lost cohort represents recoverable revenue

**Recommendations:**
1. Enrol Champions in a VIP programme (free shipping, early access)
2. Re-engage At Risk customers with a targeted discount within 30 days of their purchase anniversary
3. Convert Promising customers (recent, infrequent) with follow-up product recommendations within 2 weeks of first purchase

---

## 8. Limitations & Future Work

| Limitation | Future improvement |
|---|---|
| Static dataset — no live updates | Meltano + scheduled ingestion from Olist API |
| No SCD tracking on dimensions | dbt snapshots on dim_customer and dim_seller for Type 2 SCD |
| 1.9% of products have no English category | Expand translation table or apply ML-based translation |
| Single review per order (deduplication keeps latest) | Aggregate review sentiment across all reviews per order |
| No orchestration | GitHub Actions or Airflow DAG to schedule ingestion + dbt run + tests |
