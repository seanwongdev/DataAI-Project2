# Star Schema Design

## Business Process
Sales transactions on the Olist Brazilian e-commerce platform.

## Grain
One row per order item — the most atomic measurable event.
Defined by `(order_id, order_item_id)`.

## Schema Diagram

```
                    ┌─────────────────┐
                    │   DimCustomer   │
                    │ customer_key    │
                    │ customer_id     │
                    │ city, state     │
                    └────────┬────────┘
                             │
┌──────────────┐    ┌────────▼────────┐    ┌──────────────────┐
│  DimProduct  │    │   FactOrders    │    │    DimSeller     │
│ product_key  ├───►│ order_item_key  │◄───┤ seller_key       │
│ category_en  │    │ customer_key    │    │ seller_id        │
│ name         │    │ product_key     │    │ city, state      │
└──────────────┘    │ seller_key      │    └──────────────────┘
                    │ date_key        │
┌──────────────┐    │ price           │
│   DimDate    │    │ freight_value   │
│ date_key     ├───►│ total_amount    │
│ year, month  │    │ order_status    │
│ quarter, dow │    │ review_score    │
└──────────────┘    └─────────────────┘
```

## Fact Table Construction

`FactOrders` is built from three source tables. The grain table (`olist_order_items`) is always the left table — no grain rows are ever dropped.

```
olist_order_items (grain — left table)
  LEFT JOIN olist_orders ON order_id        ← adds order_date, order_status
  LEFT JOIN olist_order_reviews ON order_id ← adds review_score (nullable)
```

**Why LEFT JOIN throughout:**
- Every order item must be preserved
- Not every order has a review — nulls are acceptable for review_score
- Silently dropping grain rows would corrupt all downstream aggregations

## Dimension Sources

| Dimension   | Source Tables                                         | Notes                              |
|-------------|-------------------------------------------------------|------------------------------------|
| DimCustomer | olist_customers                                       | city/state from customer record    |
| DimProduct  | olist_products + product_category_name_translation    | English category name joined in    |
| DimSeller   | olist_sellers                                         | city/state from seller record      |
| DimDate     | Generated from order_purchase_timestamp               | year, month, quarter, day of week  |

## Tables Not Used in Star Schema

| Table                  | Reason                                                                 |
|------------------------|------------------------------------------------------------------------|
| olist_order_payments   | Multiple rows per order (installments/payment types) — breaks grain    |
| olist_geolocation      | city/state folded directly into DimCustomer and DimSeller              |
