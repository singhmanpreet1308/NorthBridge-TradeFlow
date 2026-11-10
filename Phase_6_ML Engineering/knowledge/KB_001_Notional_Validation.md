# KB-001: Notional Validation and Reconciliation

Version: 1.1
Domain: Trade Validation
Rule ID: DEMO_NOTIONAL_MISMATCH
Source: NorthBridge TradeFlow Phase 3 validation implementation

## Purpose

Detect differences between a captured trade notional and
the notional recorded in the independent confirmation.

## Validation Logic

The validation pipeline compares the captured notional
against the independent confirmation.

If the absolute difference exceeds 0.01, the rule
DEMO_NOTIONAL_MISMATCH is triggered.

## Example: T-1001

Original captured notional: GBP 100,000,000
Independent confirmation: GBP 10,000,000

Expected validation outcome: BLOCK

T-1001 version 1 was blocked because the captured notional
differed from the confirmation by GBP 90,000,000, which exceeds
the 0.01 tolerance and triggers DEMO_NOTIONAL_MISMATCH.

The original trade must be investigated before being
considered eligible for simulated reporting.

## Operational Guidance

1. Review the captured trade and independent confirmation.
2. Identify the source of the notional discrepancy.
3. Escalate the exception to an authorised reviewer.
4. Record an approved amendment where appropriate.
5. Revalidate the corrected trade.
6. Preserve the original trade version and audit evidence.

## Limitations

This is a demonstration validation rule, not a claim
that a regulatory authority would reject the trade.

The AI assistant must not approve amendments, change
trade records or submit reports automatically.
