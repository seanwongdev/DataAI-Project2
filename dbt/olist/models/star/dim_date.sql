SELECT DISTINCT
      DATE(order_purchase_timestamp)                          AS order_date,
      EXTRACT(YEAR FROM order_purchase_timestamp)             AS year,
      EXTRACT(MONTH FROM order_purchase_timestamp)            AS month,
      EXTRACT(QUARTER FROM order_purchase_timestamp)          AS quarter,
      EXTRACT(DAYOFWEEK FROM order_purchase_timestamp)        AS day_of_week
  FROM {{ source('bronze', 'raw_orders') }}
  WHERE order_purchase_timestamp IS NOT NULL
