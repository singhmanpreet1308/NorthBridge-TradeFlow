# KB-004: Simulated Reporting Eligibility

Version: 1.0
Domain: Regulatory Reporting (Simulated)
Rule ID: RULE-TOBE-003, RULE-TOBE-006, RULE-TOBE-008, RULE-AMD-013
Source: NorthBridge TradeFlow Design.md, Business Rules and Reporting requirements

## Purpose

Explain when a trade version may be included in a simulated
reporting submission and why blocked trades are held back.

## Eligibility Rules

- RULE-TOBE-003: Failed validation blocks simulated reporting.
- RULE-TOBE-006: Revalidation is mandatory after amendment.
- RULE-AMD-013: Amended trades must pass validation before simulated reporting.
- RULE-TOBE-008: Simulated reporting outcomes must be distinguishable
  from internal validation results.

A trade version is eligible for simulated reporting only when:

1. Its latest validation status is PASS.
2. It has no unresolved blocking exception.
3. It is not cancelled.

## Reporting Hold

A trade with validation status BLOCK is held in quarantine and
is not submitted. The hold is released only by an approved
amendment that passes revalidation, never by overriding the rule.

## Example: T-1001 Reporting Status

Version 1 (GBP 100,000,000) was blocked and is not eligible.
Version 2 (GBP 10,000,000) passed revalidation and is the version
eligible for simulated reporting.

## Limitations

Reporting in this project is simulated. A BLOCK result is an
internal control outcome, not a rejection by a regulator or
trade repository. The AI assistant must not submit reports.
