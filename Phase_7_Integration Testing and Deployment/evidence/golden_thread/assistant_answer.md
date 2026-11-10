# Assistant answer (TemplateLLM (offline stub))

**Question:** Why was T-1001 blocked, and is the current version eligible for reporting?

**Answer** - Template answer assembled from evidence tags only.
Version 1 was blocked [QUARANTINE BATCH-60FD5666D0A1FBAD].
The current version passed revalidation [CURATED T-1001 v2].
The applicable procedure is documented [KB-001 v1.1 - Example: T-1001].
**Model risk (separate from validation)** - see [MODEL 1.0.0].
**Evidence gaps** - None.

## Citation check

```json
{
  "citations_used": [
    "CURATED T-1001 v2",
    "KB-001 v1.1 - Example: T-1001",
    "MODEL 1.0.0",
    "QUARANTINE BATCH-60FD5666D0A1FBAD"
  ],
  "unknown_citations": [],
  "warnings": []
}
```

## Evidence pack sent to the LLM

```text
EVIDENCE

== TRADE RECORDS AND VALIDATION HISTORY ==
[QUARANTINE BATCH-60FD5666D0A1FBAD]
  trade: {"trade_id": "T-1001", "trade_version": 1, "trade_status": "CAPTURED", "notional_amount": 100000000.0, "currency": "GBP", "product_type": "GBP_IRS", "counterparty_id": "CP-004", "effective_date": "2026-09-23", "maturity_date": "2036-09-23", "amendment_reason": null, "created_by": "trader_01"}
  validation: {"detected_rules": "[\"DEMO_NOTIONAL_MISMATCH\"]", "validation_status": "BLOCK", "validation_run_id": "VAL-115729AE7639", "validated_at_utc": "2026-11-10T15:25:22.716589+00:00", "source_file": "raw/trades/sample_trades.csv"}
[CURATED T-1001 v2]
  trade: {"trade_id": "T-1001", "trade_version": 2, "trade_status": "AMENDED", "notional_amount": 10000000.0, "currency": "GBP", "product_type": "GBP_IRS", "counterparty_id": "CP-004", "effective_date": "2026-09-23", "maturity_date": "2036-09-23", "amendment_reason": "DEMO_NOTIONAL_MISMATCH", "created_by": "trader_01"}
  validation: {"detected_rules": "[]", "validation_status": "PASS", "validation_run_id": "VAL-90BA7E7183AC", "validated_at_utc": "2026-10-14T12:36:59.780679+00:00", "source_file": "amendments/T1001_v2.csv"}

== MODEL RISK (predictive score, NOT a validation outcome) ==
[MODEL 1.0.0]
  {"trade_id": "T-1001", "scored_version": 2, "risk_score": 0.078752, "risk_band": "Not Flagged", "prediction": 0, "threshold": 0.1, "model_version": "1.0.0"}

== KNOWLEDGE NOTES ==
[KB-001 v1.1 - Example: T-1001] (source: KB_001_Notional_Validation.md#Example: T-1001)
Original captured notional: GBP 100,000,000
Independent confirmation: GBP 10,000,000

Expected validation outcome: BLOCK

T-1001 version 1 was blocked because the captured notional
differed from the confirmation by GBP 90,000,000, which exceeds
the 0.01 tolerance and triggers DEMO_NOTIONAL_MISMATCH.

The original trade must be investigated before being
considered eligible for simulated reporting.

[KB-003 v1.0 - Example: T-1001 Amendment] (source: KB_003_Trade_Amendments.md#Example: T-1001 Amendment)
Version 1 was captured with notional GBP 100,000,000 and blocked
by DEMO_NOTIONAL_MISMATCH against a confirmation of GBP 10,000,000.

Version 2 was created as an amendment:

- Trade status: AMENDED
- Amendment reason: DEMO_NOTIONAL_MISMATCH
- Corrected notional: GBP 10,000,000
- Source file: amendments/T1001_v2.csv
- Revalidation result: PASS (validation run VAL-90BA7E7183AC)

Version 1 remains in quarantine as audit evidence.

[KB-004 v1.0 - Example: T-1001 Reporting Status] (source: KB_004_Simulated_Reporting.md#Example: T-1001 Reporting Status)
Version 1 (GBP 100,000,000) was blocked and is not eligible.
Version 2 (GBP 10,000,000) passed revalidation and is the version
eligible for simulated reporting.

[KB-001 v1.1 - Validation Logic] (source: KB_001_Notional_Validation.md#Validation Logic)
The validation pipeline compares the captured notional
against the independent confirmation.

If the absolute difference exceeds 0.01, the rule
DEMO_NOTIONAL_MISMATCH is triggered.

[KB-002 v1.0 - Validation Rules] (source: KB_002_Trade_Validation_Rules.md#Validation Rules)
| Rule ID | Check | Failure condition |
|---------|-------|-------------------|
| DQ-001 | Trade identifier | trade_id is missing or blank |
| DQ-004 | Notional amount | notional_amount is missing, zero or negative |
| DQ-005 | Currency scope | currency is not GBP (demonstration scope) |
| DQ-006 | Date order | maturity_date is missing or not after effective_date |
| DQ-007 | Fixed rate range | fixed_rate is missing or outside 0 < rate <= 0.15 |
| DQ-008 | Fixed-leg direction | pay_receive_fixed is not PAY or RECEIVE |
| DQ-009 | Mandatory fields | counterparty_id or floating_rate_index is missing |

Confirmation reconciliation is applied after these checks.
A notional difference against the independent confirmation
raises DEMO_NOTIONAL_MISMATCH (see KB-001).

```
