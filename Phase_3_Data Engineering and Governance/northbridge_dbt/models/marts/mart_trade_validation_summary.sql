
{{ config(materialized='view') }}

WITH validation_audit AS (

    SELECT
        BATCH_ID,
        VALIDATION_RUN_ID,
        VALIDATED_AT_UTC,
        VALIDATION_POLICY_VERSION,
        TOTAL_TRADES,
        CURATED_RECORDS,
        QUARANTINE_RECORDS,
        MANIFEST_TESTS_PASSED,
        MANIFEST_TESTS_TOTAL,
        STATUS
    FROM {{ ref('trade_validation_audit') }}

),

validation_summary AS (

    SELECT
        *,

        ROUND(
            100.0 * CURATED_RECORDS
            / NULLIF(TOTAL_TRADES, 0),
            2
        ) AS ACCEPTANCE_RATE_PCT,

        ROUND(
            100.0 * QUARANTINE_RECORDS
            / NULLIF(TOTAL_TRADES, 0),
            2
        ) AS QUARANTINE_RATE_PCT,

        CASE
            WHEN TOTAL_TRADES =
                 CURATED_RECORDS + QUARANTINE_RECORDS
            THEN 'PASS'
            ELSE 'FAIL'
        END AS RECONCILIATION_STATUS

    FROM validation_audit

)

SELECT *
FROM validation_summary
