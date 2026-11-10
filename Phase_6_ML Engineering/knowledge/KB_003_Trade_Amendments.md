# KB-003: Trade Amendments and Versioning

Version: 1.0
Domain: Trade Lifecycle
Rule ID: RULE-AMD-009, RULE-AMD-010, RULE-AMD-011, RULE-AMD-012, RULE-AMD-013, RULE-AMD-016, RULE-AMD-017
Source: NorthBridge TradeFlow Design.md, Section 7 (Amendment and Cancellation)

## Purpose

Define how a blocked or incorrect trade is corrected through an
approved amendment that creates a new trade version.

## Amendment Rules

- RULE-AMD-009: Material amendments require human approval.
- RULE-AMD-010: Trade versions must never be overwritten.
- RULE-AMD-011: An approved amendment creates a new trade version.
- RULE-AMD-012: Every approval decision requires an audit record.
- RULE-AMD-013: Amended trades must pass validation before simulated reporting.
- RULE-AMD-016: Stale-version changes must be rejected.
- RULE-AMD-017: Rejected corrections must not alter trade data.

## Amendment Workflow

1. Trade Operations retrieves the current trade version.
2. An analyst submits an amendment request with the proposed values and reason.
3. The request is routed to an authorised approver.
4. The approver reviews the original values, proposed values and evidence.
5. If approved, the next trade version is created; the original stays immutable.
6. The amended version returns to the validation engine for revalidation.
7. If revalidation passes, the trade becomes eligible for simulated reporting.
8. If revalidation fails, the trade remains on hold with an exception record.

If the approver rejects the request, no new version is created,
the rejection reason is recorded and reporting stays blocked.

## Example: T-1001 Amendment

Version 1 was captured with notional GBP 100,000,000 and blocked
by DEMO_NOTIONAL_MISMATCH against a confirmation of GBP 10,000,000.

Version 2 was created as an amendment:

- Trade status: AMENDED
- Amendment reason: DEMO_NOTIONAL_MISMATCH
- Corrected notional: GBP 10,000,000
- Source file: amendments/T1001_v2.csv
- Revalidation result: PASS (validation run VAL-90BA7E7183AC)

Version 1 remains in quarantine as audit evidence.

## Limitations

The AI assistant can explain the amendment history but must not
create, approve or reject amendments.
