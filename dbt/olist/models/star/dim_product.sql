SELECT
      p.product_id,
      t.string_field_1                    AS category,
      p.product_weight_g                  AS weight_g,
      p.product_length_cm                 AS length_cm,
      p.product_height_cm                 AS height_cm,
      p.product_width_cm                  AS width_cm
  FROM {{ source('bronze', 'raw_products') }} p
  LEFT JOIN {{ source('bronze', 'raw_product_category_translation') }} t
      ON p.product_category_name = t.string_field_0
