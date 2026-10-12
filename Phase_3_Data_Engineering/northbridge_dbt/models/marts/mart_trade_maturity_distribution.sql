
{{ config(materialized='view') }}

WITH trades AS (

    SELECT
        TRADE_ID,
        CURRENCY,
        NOTIONAL_AMOUNT,
        REMAINING_MATURITY_YEARS
    FROM {{ ref('int_trade_enriched') }}

),

classified AS (

    SELECT
        *,
        CASE
            WHEN REMAINING_MATURITY_YEARS IS NULL
                THEN 'Unknown'
            WHEN REMAINING_MATURITY_YEARS < 0
                THEN 'Matured'
            WHEN REMAINING_MATURITY_YEARS <= 1
                THEN '0-1 Year'
            WHEN REMAINING_MATURITY_YEARS <= 3
                THEN '1-3 Years'
            WHEN REMAINING_MATURITY_YEARS <= 5
                THEN '3-5 Years'
            WHEN REMAINING_MATURITY_YEARS <= 10
                THEN '5-10 Years'
            ELSE '10+ Years'
        END AS MATURITY_BUCKET
    FROM trades

)

SELECT
    CURRENCY,
    MATURITY_BUCKET,
    COUNT(*) AS TOTAL_TRADES,
    SUM(ABS(NOTIONAL_AMOUNT)) AS GROSS_NOTIONAL
FROM classified
GROUP BY
    CURRENCY,
    MATURITY_BUCKET
