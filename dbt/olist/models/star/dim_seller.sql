SELECT
      seller_id,
      seller_city     AS city,
      seller_state    AS state
  FROM {{ source('bronze', 'raw_sellers') }}
