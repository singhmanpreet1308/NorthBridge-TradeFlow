
{{ config(materialized='view') }}

WITH trades AS (

    SELECT *
    FROM {{ ref('stg_trades_validated') }}

),

enriched AS (

    SELECT
        *,

        ROUND(
            DATEDIFF('day', EFFECTIVE_DATE, MATURITY_DATE) / 365.25,
            2
        ) AS SWAP_TENOR_YEARS,

        ROUND(
            DATEDIFF('day', CURRENT_DATE(), MATURITY_DATE) / 365.25,
            2
        ) AS REMAINING_MATURITY_YEARS

    FROM trades

)

SELECT *
FROM enriched
