
{{ config(materialized='view') }}

WITH trades AS (

    SELECT
        TRADE_ID,
        CURRENCY,
        NOTIONAL_AMOUNT,
        SWAP_TENOR_YEARS,
        MATURITY_DATE
    FROM {{ ref('int_trade_enriched') }}

),

portfolio_summary AS (

    SELECT
        CURRENCY,
        COUNT(*) AS TOTAL_TRADES,
        SUM(ABS(NOTIONAL_AMOUNT)) AS GROSS_NOTIONAL,
        AVG(ABS(NOTIONAL_AMOUNT)) AS AVG_TRADE_NOTIONAL,
        ROUND(AVG(SWAP_TENOR_YEARS), 2) AS AVG_SWAP_TENOR_YEARS,
        COUNT_IF(MATURITY_DATE < CURRENT_DATE()) AS MATURED_TRADES,
        COUNT_IF(MATURITY_DATE >= CURRENT_DATE()) AS NOT_YET_MATURED_TRADES

    FROM trades
    GROUP BY CURRENCY

)

SELECT *
FROM portfolio_summary
