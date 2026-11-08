# NorthBridge TradeFlow — Data Quality Plan

## 1. Purpose

This document defines the data-quality controls implemented in Phase 3 of NorthBridge TradeFlow.

The objective is to ensure that only validated synthetic OTC interest-rate swap trades enter the curated dataset and Snowflake analytics pipeline.

## 2. Data Quality Architecture

The pipeline processes data through the following stages:

1. Read source trades and independent confirmations.
2. Verify source integrity and validation requirements.
3. Apply trade-level validation rules.
4. Separate accepted and rejected records.
5. Generate validation audit metadata.
6. Verify the completed batch before Snowflake ingestion.
7. Execute dbt transformations and tests.

## 3. Data Quality Dimensions

| Dimension    | Validation Objective                                        |
| ------------ | ----------------------------------------------------------- |
| Completeness | Check required trade information is present                 |
| Uniqueness   | Detect duplicate trade identifiers                          |
| Validity     | Check trade attributes against validation rules             |
| Consistency  | Compare applicable values with independent confirmations    |
| Integrity    | Verify source checksums and batch metadata                  |
| Traceability | Associate outputs with batch and validation run identifiers |

The precise trade-level rules and thresholds are maintained in the Python validation implementation.

## 4. Validation Controls

### Source Integrity

The pipeline verifies source files using SHA-256 checksums.

The recorded source checksums support detection of unexpected source changes.

### Trade-Level Validation

Each trade receives a validation outcome.

- `PASS`: Accepted into the curated dataset.
- `BLOCK`: Excluded from curated ingestion and placed in quarantine.

### Batch Metadata

The pipeline records:

- Batch identifier.
- Validation run identifier.
- Validation policy version.
- Source file references and checksums.
- Total processed records.
- Curated and quarantined record counts.
- Validation timestamp and outcome.

### Completion Marker

The `_SUCCESS.json` marker indicates that the validation batch completed successfully.

The Snowflake ingestion script checks the marker and verifies relevant metadata before loading data.

## 5. Verified Validation Results

The completed synthetic trade batch produced:

| Metric                |    Result |
| --------------------- | --------: |
| Source trades         |        50 |
| Curated trades        |        49 |
| Quarantined trades    |         1 |
| Acceptance rate       |       98% |
| Manifest tests passed |   10 / 10 |
| Validation status     | VALIDATED |

Batch identifier:

`BATCH-60FD5666D0A1FBAD`

Validation run identifier:

`VAL-E6532CDFF204`

Validation policy version: `1.1`

These results represent the verified project test batch, not a production financial dataset.

## 6. Quarantine Strategy

Records that do not satisfy blocking validation requirements are separated from the curated dataset.

Quarantine output:

`quarantine/trades/{batch_id}/blocked_trades.csv`

Curated output:

`curated/trades/{batch_id}/validated_trades.csv`

This design prevents failed records from being included in downstream analytics while preserving them for investigation.

## 7. Snowflake Ingestion Quality Controls

Before ingestion, the pipeline:

- Verifies the batch completion marker.
- Confirms the expected batch and validation run identifiers.
- Checks that curated records have `PASS` status.
- Checks trade-level integrity.
- Counts previously loaded records for the validation run.

If the complete batch already exists, ingestion is skipped.

If an unexpected partial batch is detected, the pipeline raises an error instead of silently duplicating records.

## 8. dbt Data Quality Tests

The staging model includes the following tests:

| Field                 | Test                 |
| --------------------- | -------------------- |
| `TRADE_ID`          | Not null             |
| `TRADE_ID`          | Unique               |
| `VALIDATION_STATUS` | Not null             |
| `VALIDATION_STATUS` | Accepted value: PASS |

Verified dbt build results:

- 8 SQL models.
- 1 audit seed.
- 4 data-quality tests.
- 13 successful operations.
- 0 failed operations.

## 9. Auditability and Monitoring

The implementation produces validation summaries, completion metadata and ingestion audit events.

Ingestion outcomes include:

- `STARTED`
- `SUCCESS`
- `SKIPPED`
- `FAILED`

The Python orchestrator runs validation, ingestion and dbt sequentially, stopping when a stage returns an error.

## 10. Known Limitations and Future Enhancements

The current implementation uses synthetic data and a limited test batch.

Potential future enhancements include:

- Expanded automated validation scenarios.
- Historical data-quality trend reporting.
- Alerting for recurring or significant failures.
- Automated reconciliation with additional independent sources.
- Centralized monitoring dashboards.

These are future improvements, not capabilities claimed to be implemented in Phase 3.

## 11. Acceptance Criteria

Phase 3 data-quality controls are considered successfully tested when:

- Validation completes with expected batch outputs.
- Rejected records are excluded from curated ingestion.
- Batch metadata and completion marker are verified.
- Duplicate Snowflake ingestion is prevented.
- dbt models and tests complete successfully.
- The end-to-end orchestrator reports `PIPELINE STATUS: SUCCESS`.

All these criteria were satisfied during the verified Phase 3 execution.
