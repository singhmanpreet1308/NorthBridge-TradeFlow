
{{ config(materialized='view') }}

WITH trades AS (

    SELECT
        TRADE_ID,
        COUNTERPARTY_ID,
        CURRENCY,
        NOTIONAL_AMOUNT
    FROM {{ ref('int_trade_enriched') }}

),

counterparty_exposure AS (

    SELECT
        COUNTERPARTY_ID,
        CURRENCY,
        COUNT(*) AS TOTAL_TRADES,
        SUM(ABS(NOTIONAL_AMOUNT)) AS GROSS_NOTIONAL,
        AVG(ABS(NOTIONAL_AMOUNT)) AS AVG_TRADE_NOTIONAL

    FROM trades

    GROUP BY
        COUNTERPARTY_ID,
        CURRENCY

)

SELECT *
FROM counterparty_exposure
