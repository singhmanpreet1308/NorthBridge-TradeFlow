
{{ config(materialized='view') }}

WITH ranked_trades AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY TRADE_ID
            ORDER BY TRADE_VERSION DESC, VALIDATED_AT_UTC DESC
        ) AS VERSION_RANK

    FROM {{ ref('stg_trades_validated') }}

)

SELECT *
EXCLUDE (VERSION_RANK)
FROM ranked_trades
WHERE VERSION_RANK = 1
