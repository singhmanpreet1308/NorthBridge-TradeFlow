# NorthBridge TradeFlow — Validation Rules

## 1. Objective

Document the validation controls used to identify trade-data errors, confirmation discrepancies and simulated reporting issues before a trade proceeds through the reporting lifecycle.

**Scope:** Synthetic GBP interest rate swaps.

**Regulatory reference:** UK EMIR, for learning and demonstration purposes only.

## 2. Validation Categories

### A. Data Quality Controls

| Rule ID | Description                                               | Failure Action |
| ------- | --------------------------------------------------------- | -------------- |
| DQ-001  | Trade ID must not be missing                              | BLOCK          |
| DQ-004  | Notional amount must be positive                          | BLOCK          |
| DQ-005  | Currency must be GBP for the demonstration scope          | BLOCK          |
| DQ-006  | Maturity date must be later than effective date           | BLOCK          |
| DQ-007  | Fixed rate must be greater than 0 and no more than 0.15   | BLOCK          |
| DQ-008  | Fixed-leg direction must be PAY or RECEIVE                | BLOCK          |
| DQ-009  | Counterparty ID and floating-rate index must be populated | BLOCK          |

These controls are implemented in the Phase 3 Python validation process. The numeric rate range and GBP-only restriction are project-specific controls, not general UK EMIR requirements.

### B. Confirmation Reconciliation Controls

| Rule ID                      | Description                                                               | Failure Action |
| ---------------------------- | ------------------------------------------------------------------------- | -------------- |
| DEMO_NOTIONAL_MISMATCH       | Captured notional differs from independent confirmation by more than 0.01 | BLOCK          |
| RECON_MISSING_CONFIRMATION   | No matching confirmation found                                            | BLOCK          |
| RECON_DUPLICATE_CONFIRMATION | More than one matching confirmation found                                 | BLOCK          |

### C. Proposed Simulated Reporting Controls

| Rule ID         | Description                                     | Proposed Action |
| --------------- | ----------------------------------------------- | --------------- |
| DEMO-REPORT-001 | Required reporting identifier unavailable       | HOLD            |
| DEMO-REPORT-002 | Counterparty regulatory identifier not verified | HOLD            |
| DEMO-REPORT-003 | Product classification mapping unresolved       | HOLD            |
| DEMO-REPORT-004 | Required reporting field missing or invalid     | HOLD            |

These reporting controls are proposed for Phase 4 and are not yet implemented or tested. They must not be represented as official UK EMIR validation rule IDs.

## 3. T-1001 Validation Example

**Original version:** T-1001 v1
**Captured notional:** GBP 100,000,000
**Independent confirmation:** GBP 10,000,000
**Detected rule:** DEMO_NOTIONAL_MISMATCH
**Outcome:** BLOCK and quarantine

**Corrected version:** T-1001 v2
**Notional:** GBP 10,000,000
**Outcome:** PASS after approved amendment and revalidation

The original version remains preserved in the quarantine evidence. The corrected version is available in Snowflake for current-trade analytics.

## 4. Regulatory Boundary

NorthBridge TradeFlow uses UK EMIR as a reporting reference. Internal identifiers, demonstration validation rules and simulated reporting outcomes are not evidence of regulatory acceptance.

Actual UK EMIR reporting requires verification against the applicable technical standards, field definitions, identifier requirements and reporting validation rules.
