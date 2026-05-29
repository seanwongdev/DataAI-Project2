SELECT
      customer_id,
      customer_unique_id,
      customer_city       AS city,
      customer_state      AS state
  FROM {{ source('bronze', 'raw_customers') }}
