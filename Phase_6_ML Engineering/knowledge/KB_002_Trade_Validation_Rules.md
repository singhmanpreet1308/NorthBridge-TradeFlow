# KB-002: Trade Validation Rules

Version: 1.0
Domain: Trade Validation
Rule ID: DQ-001, DQ-004, DQ-005, DQ-006, DQ-007, DQ-008, DQ-009
Source: NorthBridge TradeFlow Phase 3 validation implementation (pipeline/validate.py)

## Purpose

Describe the data-quality rules applied to every captured trade
before it can be published to the curated layer or considered
for simulated reporting.

## Validation Rules

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

## Validation Outcome

A trade with no detected rules receives validation status PASS
and is written to the curated layer.

A trade with one or more detected rules receives validation
status BLOCK. It is written to the quarantine layer
(blocked_trades.csv) together with the detected rule IDs,
the batch ID and the validation run ID.

A blocked trade is held from simulated reporting until an
approved amendment passes revalidation (see KB-003 and KB-004).

## Operational Guidance

1. Read the detected rule IDs on the quarantined record.
2. Look up each rule in this note to understand the failure.
3. Compare the failing field with the source system and confirmation.
4. Raise an exception and follow the escalation path in KB-005.

## Limitations

DQ-005 and DQ-007 are demonstration-only limits chosen for this
project. They are not market or regulatory thresholds.
