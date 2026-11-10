# KB-005: Exception Handling and Escalation

Version: 1.0
Domain: Operations Control
Rule ID: RULE-TOBE-004, RULE-TOBE-005, EX-001, EX-005
Source: NorthBridge TradeFlow Design.md, Exception Handling

## Purpose

Define who handles a validation exception, when it must be
escalated and what evidence must be retained.

## Exception Handling Steps

When validation fails:

1. Record the failed rule ID.
2. Create an exception record.
3. Hold the trade from simulated reporting.
4. Assign an exception owner in Trade Operations.
5. Record the review decision.
6. Revalidate any approved amendment.

## Escalation Path

| Level | Owner | Escalate when |
|-------|-------|---------------|
| 1 | Trade Operations analyst | Any new BLOCK result |
| 2 | Authorised approver (independent of requester) | A material correction such as a notional change is proposed |
| 3 | Operations Control lead | Revalidation fails (EX-005) or the correction is rejected (EX-001) |

Material corrections require human approval (RULE-TOBE-004).
A notional mismatch such as T-1001 is always a material correction
and must be escalated to an authorised approver.

## Audit Evidence

Original trade versions and audit events are retained
(RULE-TOBE-005). The exception record should reference the
quarantined record, the batch ID, the validation run ID and
the confirmation used as evidence.

## Limitations

The AI assistant may summarise the exception and recommend the
escalation level. It must not assign owners, approve corrections
or close exceptions.
