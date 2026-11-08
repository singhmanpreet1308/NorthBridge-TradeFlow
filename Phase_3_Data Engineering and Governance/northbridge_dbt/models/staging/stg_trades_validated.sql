
{{ config(materialized='view') }}

SELECT *
FROM {{ source('curated', 'trades_validated') }}
WHERE VALIDATION_STATUS = 'PASS'
