
{{ config(materialized='view') }}

WITH trade_versions AS (

    SELECT
        TRADE_ID,
        TRADE_VERSION,
        TRADE_DATE,
        TRADE_STATUS,
        NOTIONAL_AMOUNT,
        VALIDATION_RUN_ID,
        VALIDATED_AT_UTC,

        ROW_NUMBER() OVER (
            PARTITION BY TRADE_ID
            ORDER BY TRADE_VERSION DESC, VALIDATED_AT_UTC DESC
        ) AS VERSION_RANK,

        COUNT(*) OVER (
            PARTITION BY TRADE_ID
        ) AS VERSION_COUNT

    FROM {{ ref('stg_trades_validated') }}

)

SELECT
    *,
    CASE
        WHEN VERSION_RANK = 1 THEN TRUE
        ELSE FALSE
    END AS IS_LATEST_VERSION

FROM trade_versions
