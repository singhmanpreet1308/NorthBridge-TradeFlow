
# NorthBridge TradeFlow — Reject Handling & Resubmission

## 1. Objective

Define how trade exceptions are detected, investigated, corrected, revalidated and resubmitted within the NorthBridge TradeFlow demonstration.

**Scope:** Synthetic GBP interest rate swaps.

**Regulatory reference:** UK EMIR. All regulatory reporting submissions and outcomes are simulated.

## 2. Exception Categories

| Category                      | Description                                         | Handling              |
| ----------------------------- | --------------------------------------------------- | --------------------- |
| Internal Validation Failure   | Trade fails a data-quality rule                     | BLOCK and quarantine  |
| Confirmation Break            | Trade terms differ from an independent confirmation | BLOCK and investigate |
| Simulated Reporting Rejection | Demonstration report fails a reporting rule         | REJECT and review     |

A trade failing internal validation is not automatically a regulatory reporting rejection.

## 3. Exception Handling Workflow

1. **Detect:** Execute the appropriate validation or reporting control and record the rule ID.
2. **Log:** Save trade ID, version, source, timestamp, detected rule and exception status.
3. **Assign:** Route the issue to the responsible Trade Operations reviewer.
4. **Investigate:** Compare the captured trade with independent confirmation and supporting evidence.
5. **Approve:** Require documented human approval before making a correction.
6. **Amend:** Create a new trade version without overwriting the original.
7. **Revalidate:** Apply the validation controls again.
8. **Resubmit:** Create a new simulated reporting attempt only when the corrected trade meets the required reporting checks.
9. **Close:** Record the final simulated outcome and retain the complete audit history.

The reporting resubmission stage is a proposed workflow until simulated submission records and execution evidence are implemented.

## 4. T-1001 — Notional Mismatch Example

| Stage                       | T-1001 outcome                            |
| --------------------------- | ----------------------------------------- |
| Original Capture            | Version 1, GBP 100,000,000                |
| Confirmation Check          | Expected GBP 10,000,000                   |
| Detected Rule               | DEMO_NOTIONAL_MISMATCH                    |
| Initial Outcome             | BLOCK and quarantine                      |
| Human Approval              | Recorded in T1001_Approval.json           |
| Amendment                   | Version 2, GBP 10,000,000                 |
| Revalidation                | PASS                                      |
| Snowflake Load              | Corrected version accepted                |
| dbt Analytics               | Version 2 available in current-trade view |
| Simulated Reporting Outcome | Not yet executed                          |

T-1001 demonstrates internal exception resolution. It must not be described as an externally rejected and resubmitted regulatory transaction.

## 5. Proposed Reporting Statuses

| Status                | Definition                                                  |
| --------------------- | ----------------------------------------------------------- |
| READY                 | Report passed the project's required pre-submission checks  |
| HOLD                  | Report cannot proceed because of unresolved information     |
| SUBMITTED_SIMULATED   | Demonstration submission attempt created                    |
| ACCEPTED_SIMULATED    | Demonstration reporting checks passed                       |
| REJECTED_SIMULATED    | Demonstration reporting checks failed                       |
| RESUBMITTED_SIMULATED | Corrected report submitted for another simulated evaluation |

These are NorthBridge project statuses, not official trade repository response codes.

## 6. Audit Requirements

Every exception or reporting attempt should retain the trade ID, version, rule ID, processing timestamp, assigned reviewer, approval reference, previous outcome and subsequent outcome.

Store immutable evidence wherever possible. Any replay must use stable identifiers to prevent duplicate reporting attempts.

## 7. Responsibilities

| Role                            | Responsibility                                         |
| ------------------------------- | ------------------------------------------------------ |
| Trade Operations                | Investigate and propose corrections                    |
| Operations Approver             | Authorise amendments                                   |
| Data Engineering                | Maintain data lineage and processing integrity         |
| Regulatory Reporting Operations | Review simulated reporting outcomes                    |
| Compliance                      | Review regulatory mappings and unresolved requirements |

## 8. Limitations

- No external trade repository or ARM has been connected.
- No actual UK EMIR report has been submitted.
- Reporting rejection and resubmission remain design-stage capabilities until executed and tested.
- Internal validation success does not guarantee acceptance under UK EMIR.
- Production regulatory requirements must be verified against applicable authoritative documentation.
