WITH latest_reviews AS (
    SELECT
        order_id,
        review_score,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_creation_date DESC) AS rn
    FROM {{ source('bronze', 'raw_order_reviews') }}
)

SELECT
    oi.order_id,
    oi.order_item_id,
    o.customer_id,
    oi.product_id,
    oi.seller_id,
    DATE(o.order_purchase_timestamp)    AS order_date,
    o.order_status,
    oi.price,
    oi.freight_value,
    oi.price + oi.freight_value         AS total_amount,
    r.review_score
FROM {{ source('bronze', 'raw_order_items') }} oi
LEFT JOIN {{ source('bronze', 'raw_orders') }} o
    ON oi.order_id = o.order_id
LEFT JOIN latest_reviews r
    ON oi.order_id = r.order_id AND r.rn = 1
