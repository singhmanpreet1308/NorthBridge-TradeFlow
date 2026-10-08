# T1001 Trade Card

## Purpose

T-1001 demonstrates how a trade can pass basic numeric validation while containing incorrect economics. All data and reporting outcomes in this scenario are synthetic.

## Trade details

| Attribute                        | Value                           |
| -------------------------------- | ------------------------------- |
| Trade ID                         | T-1001                          |
| Source reference                 | OMS-1001                        |
| Counterparty                     | CP-004                          |
| Product                          | GBP interest-rate swap          |
| Currency                         | GBP                             |
| Trade date                       | 2026-09-21                      |
| Effective date                   | 2026-09-23                      |
| Maturity date                    | 2036-09-23                      |
| Fixed rate                       | 0.033251, equivalent to 3.3251% |
| Floating-rate index              | SONIA                           |
| Fixed-leg direction              | PAY                             |
| Payment frequency                | ANNUAL                          |
| Original version                 | 1                               |
| Original status                  | CAPTURED                        |
| Captured notional                | GBP 100,000,000                 |
| Independently confirmed notional | GBP 10,000,000                  |

## Defect and evidence

The captured notional is ten times the independently confirmed amount.

Supporting files:

- `sample_trades.csv`: original T-1001 version 1.
- `seeded_errors.csv`: T-1001 defect fixture.
- `independent_confirmations.csv`: confirmation CONF-0001.
- `seeded_error_manifest.csv`: expected rule and blocking outcome.
- `Data_Dictionary.xlsx`: field definitions and validation rules.

The baseline and seeded files are separate test fixtures. Their T-1001 records must not be appended as separate historical versions.

## Expected validation

| Check                  | Expected result | Reason                                                          |
| ---------------------- | --------------- | --------------------------------------------------------------- |
| DQ-004                 | Pass            | GBP 100,000,000 is numeric and positive.                        |
| DEMO_NOTIONAL_MISMATCH | Fail and BLOCK  | Captured GBP 100,000,000 differs from confirmed GBP 10,000,000. |

These are expected results. Executed validation results must be saved separately.

## Expected lifecycle

1. Capture and retain version 1.
2. Compare the trade with its independent confirmation.
3. Record the notional mismatch and hold simulated reporting.
4. Have Trade Operations investigate the discrepancy.
5. Have Front Office confirm the intended economics.
6. Obtain authorised human approval before creating an amendment.
7. Create version 2 with notional GBP 10,000,000.
8. Preserve version 1 and link the amendment to its approval evidence.
9. Revalidate version 2.
10. Allow simulated reporting only after all required checks pass.
11. Reconcile the trade versions, exception and simulated reporting outcome.

The approval role and detailed approval controls will be finalised in Phase 2.

## Planned corrected version

| Field            | Planned value                                                         |
| ---------------- | --------------------------------------------------------------------- |
| trade_id         | T-1001                                                                |
| trade_version    | 2                                                                     |
| notional_amount  | 10000000.00                                                           |
| trade_status     | AMENDED                                                               |
| amendment_reason | Correct captured notional to match independent confirmation CONF-0001 |
| created_by       | Actual authorised user or process, recorded when created              |
| record_timestamp | Actual UTC timestamp when version 2 is created                        |

Retain the original capture timestamp and unchanged trade economics. Store approval identity, timestamp and evidence in the later approval/event model.

Version 2 is planned, not yet represented as an approved or executed amendment.

## Acceptance criteria

- Version 1 remains available with notional GBP 100,000,000.
- Confirmation CONF-0001 records notional GBP 10,000,000.
- Validation identifies DEMO_NOTIONAL_MISMATCH for version 1.
- Simulated reporting is blocked while the discrepancy remains unresolved.
- No amendment is created without recorded human approval.
- The approved correction creates version 2 without overwriting version 1.
- Each trade/version key is unique within the accepted trade history.
- Version 2 passes notional matching and all other applicable checks before simulated reporting proceeds.
- Validation, approval, amendment and reporting evidence remain traceable.

## Business need links

- BN-002: Detect trade errors earlier.
- BN-003: Improve exception resolution.
- BN-004: Preserve amendment history.
- BN-005: Improve reporting data quality.

## Current evidence status

Phase 1 fixtures establish the original notional and the independent confirmation discrepancy.

Approval, version 2 creation, revalidation and simulated reporting are later implementation activities. Their acceptance criteria remain pending until execution evidence is saved.
