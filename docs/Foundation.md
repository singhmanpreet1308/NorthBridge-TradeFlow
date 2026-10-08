# NorthBridge TradeFlow

## Phase 1 — Business and Domain Foundation

## 1. Project Overview

NorthBridge TradeFlow is an end-to-end Data and AI project
for a financial-services organisation, NorthBridge Markets.

The project demonstrates the lifecycle of an OTC trade from initial
trade capture through validation, exception handling, amendment,
simulated regulatory reporting, operational analytics, predictive
risk scoring, and AI-assisted operations support.

The initial implementation focuses on a small GBP interest-rate swap
lifecycle using synthetic data.

---

## 2. Business Problem

OTC trade-processing workflows can involve information being entered,
transferred, validated, corrected, and reconciled across multiple
operational stages.

Where trade information is manually re-keyed or inconsistently
validated, errors may enter the workflow and remain undetected until a
later stage.

This can result in:

- trade-processing exceptions;
- additional manual investigation;
- confirmation breaks;
- reporting delays;
- repeated corrections;
- reduced straight-through processing;
- poor operational traceability; and
- increased operational effort.

NorthBridge Markets therefore needs a controlled trade-processing
workflow that identifies data-quality issues earlier, preserves the
complete amendment history, and provides traceable evidence of how an
exception was investigated and resolved.

---

## 3. Proposed Solution

NorthBridge TradeFlow will demonstrate a connected processing workflow
that:

1. captures synthetic OTC trade records;
2. validates trade data against defined business rules;
3. identifies and records exceptions;
4. routes material issues for human review;
5. preserves original and amended trade versions;
6. revalidates corrected trades;
7. produces simulated reporting outcomes;
8. provides operational KPI and exception analytics;
9. predicts potential pre-submission rejection risk; and
10. provides an AI operations assistant for evidence-based trade
    investigation.

Human approval remains required for trade correction and submission-
related actions.

---

## 4. Initial Scope

The first release focuses on:

- GBP interest-rate swaps;
- approximately 50 synthetic UAT trades;
- intentionally seeded data-quality defects;
- trade capture and validation;
- exception handling;
- human-approved amendments;
- trade-version history;
- simulated reporting;
- operational analytics;
- predictive risk modelling; and
- an AI-assisted investigation workflow.

The recurring demonstration trade is T-1001.

---

## 5. Out of Scope

The following are outside the initial project release:

- live trading;
- real client or counterparty data;
- production trade execution;
- external regulatory submissions;
- production certification;
- production-grade market connectivity; and
- autonomous trade amendments or submissions.

## 6. Project Charter

### 6.1 Project Information

| Attribute           | Description                           |
| ------------------- | ------------------------------------- |
| Project Name        | NorthBridge TradeFlow                 |
| Organisation        | NorthBridge Markets                   |
| Domain              | Financial Services — OTC Derivatives |
| Product Focus       | GBP Interest Rate Swaps               |
| Project Type        | End-to-End Data and AI Solution       |
| Delivery Approach   | Agile and SDLC                        |
| Project Status      | In Progress                           |
| Data Classification | Synthetic Demonstration Data          |

### 6.2 Project Purpose

To design and demonstrate an integrated trade-processing solution
that improves data quality, operational traceability, exception
management, and decision support across the OTC trade lifecycle.

### 6.3 Business Objectives

**BO-001 — Improve Trade Data Quality**

Identify incorrect, incomplete, or inconsistent trade information
before downstream processing.

**BO-002 — Reduce Manual Processing**

Demonstrate how automated validation and standardisation can reduce
manual re-keying and repeated investigation.

**BO-003 — Improve Exception Management**

Provide a structured process for identifying, assigning, reviewing,
and resolving trade exceptions.

**BO-004 — Establish Auditability**

Preserve trade versions, validation outcomes, amendment approvals,
and processing events.

**BO-005 — Improve Operational Visibility**

Provide dashboards showing trade volumes, validation failures,
straight-through processing, simulated reporting outcomes,
and processing latency.

**BO-006 — Enable Intelligent Decision Support**

Demonstrate predictive rejection-risk scoring and an AI assistant
that supports evidence-based investigation without autonomously
changing trade records.

### 6.4 Project Scope

**In Scope**

- Synthetic GBP interest-rate swap transactions
- Trade capture and data validation
- Exception detection and investigation
- Human-approved trade amendments
- Trade versioning and audit history
- Simulated regulatory reporting
- Operational dashboards and KPI analysis
- Predictive rejection-risk modelling
- AI-assisted trade investigation

**Out of Scope**

- Live financial transactions
- Real customer or counterparty data
- Production trading systems
- External regulatory submissions
- Autonomous trade correction or submission
- Production regulatory certification

### 6.5 Expected Business Benefits

- Earlier detection of trade-data defects
- Reduced manual investigation effort
- Improved visibility of processing exceptions
- Better traceability of trade amendments
- More consistent operational reporting
- Improved support for risk-based prioritisation

These are intended benefits, not measured project outcomes.

### 6.6 Project Success Criteria

The project will be considered successful when:

1. The synthetic trade dataset is reproducible and validated.
2. Seeded trade defects are detected by the intended rules.
3. Original and amended trade versions remain traceable.
4. Simulated reporting outcomes can be reconciled.
5. Dashboard KPIs match underlying SQL calculations.
6. Predictive model performance is evaluated on held-out data.
7. The AI assistant retrieves and cites relevant evidence.
8. Core workflows pass integration and acceptance tests.
9. The complete solution can be reproduced from documented steps.

### 6.7 Key Constraints and Assumptions

- All transactions use synthetic data.
- The initial product scope is limited to GBP interest-rate swaps.
- The project uses approximately 50 UAT trades.
- Predictive modelling uses a separate synthetic history.
- Cloud-service availability and budget are confirmed in Phase 2.
- Regulatory outcomes are simulated and must not be represented
  as actual regulatory decisions.
- Human approval is required before trade amendments.

## 7. Stakeholder Identification & Analysis

### 7.1 Stakeholder Register

| ID     | Stakeholder                               | Primary Responsibility                                           | Business Need                                                 |
| ------ | ----------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| SH-001 | Front Office Trader                       | Execute trades and ensure accurate trade capture                 | Accurate trade records and timely confirmation                |
| SH-002 | Trade Operations Analyst                  | Monitor trade processing and investigate exceptions              | Early error detection and efficient exception resolution      |
| SH-003 | Middle Office / Risk Analyst              | Review trade exposure and control exceptions                     | Reliable trade data and risk visibility                       |
| SH-004 | Compliance & Regulatory Reporting Analyst | Review reportable data and simulated submission outcomes         | Complete, consistent and traceable reporting information      |
| SH-005 | Data Engineering Team                     | Build and maintain data pipelines, validation and reconciliation | Reliable data sources, quality controls and auditability      |
| SH-006 | Operations Manager / Product Owner        | Prioritise requirements and monitor operational performance      | KPI visibility, processing efficiency and controlled delivery |

### 7.2 Stakeholder Decision Responsibilities

**SH-001 — Front Office Trader**

- Reviews and confirms intended trade economics.
- Clarifies discrepancies in captured trade details.
- Provides business confirmation for proposed corrections.

**SH-002 — Trade Operations Analyst**

- Investigates validation failures.
- Assigns and tracks trade exceptions.
- Prepares amendments for authorised approval.
- Revalidates corrected trade records.

**SH-003 — Middle Office / Risk Analyst**

- Reviews material trade discrepancies.
- Assesses potential operational and risk implications.
- Escalates significant exceptions when necessary.

**SH-004 — Compliance & Regulatory Reporting Analyst**

- Reviews reporting-field completeness.
- Investigates simulated reporting exceptions.
- Verifies reporting corrections before simulated resubmission.

**SH-005 — Data Engineering Team**

- Maintains source-to-target data mappings.
- Implements validation and reconciliation controls.
- Preserves trade history and processing logs.
- Investigates technical data-quality failures.

**SH-006 — Operations Manager / Product Owner**

- Prioritises business requirements.
- Reviews operational KPIs.
- Approves project scope and acceptance criteria.
- Escalates unresolved operational issues.

### 7.3 Stakeholder Engagement Strategy

| Stakeholder                        | Influence | Interest | Engagement Approach         |
| ---------------------------------- | --------- | -------- | --------------------------- |
| Front Office Trader                | High      | High     | Regular requirement reviews |
| Trade Operations Analyst           | High      | High     | Workflow workshops and UAT  |
| Middle Office / Risk Analyst       | High      | Medium   | Risk-control reviews        |
| Compliance Analyst                 | High      | High     | Reporting-rule validation   |
| Data Engineering Team              | Medium    | High     | Technical design reviews    |
| Operations Manager / Product Owner | High      | High     | Milestone and KPI reviews   |

### 7.4 Key Stakeholder Expectations

The solution should:

1. Detect incorrect trade information before downstream processing.
2. Reduce repeated manual investigation.
3. Provide clear exception ownership and status.
4. Preserve original and amended trade records.
5. Support transparent reporting and reconciliation.
6. Provide measurable operational performance indicators.
7. Keep trade amendments under authorised human control.

### 7.5 Stakeholder Assumptions

The stakeholder roles are representative of a fictional OTC
trade-processing organisation.

The exact approval authority and segregation-of-duties model will
be finalised during Phase 2 solution design.

## 8. OTC Trade Lifecycle Primer

### 8.1 OTC Trading Overview

Over-the-Counter (OTC) derivatives are financial contracts
negotiated directly between counterparties.

NorthBridge TradeFlow focuses on GBP interest-rate swaps,
where counterparties exchange interest-payment cash flows
calculated on an agreed notional amount.

### 8.2 Trade Lifecycle Stages

**Stage 1 — Trade Capture**

A trader executes a transaction and the trade details are
recorded in the Order Management System (OMS).

Typical fields include:

- Trade ID
- Counterparty
- Product Type
- Notional Amount
- Currency
- Fixed Rate
- Floating Rate Reference
- Effective Date
- Maturity Date

**Stage 2 — Trade Validation**

The system checks whether captured trade data satisfies
the defined validation rules.

Examples:

- Mandatory fields must not be missing.
- Notional must be positive.
- Currency must be supported.
- Maturity date must be later than effective date.
- Trade identifiers must satisfy uniqueness rules.

**Stage 3 — Trade Confirmation**

The captured trade details are compared with an independent
counterparty confirmation.

The objective is to verify that both parties agree on the
economic terms of the transaction.

**Stage 4 — Exception Management**

If a discrepancy is detected, an exception is recorded.

The Trade Operations Analyst investigates the issue,
identifies the affected fields and coordinates resolution.

**Stage 5 — Trade Amendment**

Once the correct trade details are confirmed and an
authorised person approves the change, a new trade version
is created.

The original trade version must remain available for audit.

**Stage 6 — Regulatory Reporting**

Selected trade fields are mapped and validated against
the project's demonstration reporting rules.

NorthBridge TradeFlow generates simulated submission
records and reporting outcomes.

No external regulatory submission occurs.

**Stage 7 — Reconciliation**

Trade records, confirmations, amendments and simulated
reporting outcomes are compared.

Differences are investigated and recorded as exceptions
where appropriate.

### 8.3 Example — T-1001 Trade Exception

Trade ID: T-1001
Product: GBP Interest Rate Swap
Tenor: 10 Years

Intended Notional: GBP 10,000,000
Captured Notional: GBP 100,000,000

Problem:
The captured notional is ten times the intended amount.

Validation:
A basic numeric validation may pass because GBP 100,000,000
is a valid positive amount.

However, comparison against the independent confirmation
fixture identifies a notional mismatch.

Demo Rule ID:
DEMO_NOTIONAL_MISMATCH

Resolution:

1. Detect the mismatch.
2. Create an exception and hold simulated reporting.
3. Investigate the discrepancy.
4. Confirm the intended notional.
5. Obtain authorised human approval.
6. Create trade version 2 with GBP 10,000,000.
7. Preserve trade version 1.
8. Revalidate the corrected trade.
9. Generate a simulated reporting outcome.
10. Reconcile the trade and exception history.

### 8.4 Key Business Principle

A trade can be technically valid but economically incorrect.

Therefore, NorthBridge TradeFlow must support both:

1. Data-quality and format validation.
2. Business-level reconciliation against independent evidence.

The solution must also preserve amendment history and
prevent unapproved changes to trade records.

## 9. AS-IS Business Process

### 9.1 Process Overview

The NorthBridge Markets AS-IS workflow represents a
partially manual OTC trade-processing environment.

Trade information is captured in an Order Management System
(OMS) and may be manually transferred into downstream
operational and reporting processes.

Basic validation checks are performed, but discrepancies
between captured and independently confirmed trade
economics may be identified later in the workflow.

This AS-IS process is a project assumption, not an
observation of a real financial institution.

### 9.2 Current Process Activities

| Step  | Activity                                | Responsible Stakeholder          |
| ----- | --------------------------------------- | -------------------------------- |
| AS-01 | Execute OTC trade                       | Front Office Trader              |
| AS-02 | Capture trade in OMS                    | Front Office Trader              |
| AS-03 | Re-key trade details                    | Trade Operations Analyst         |
| AS-04 | Perform basic validation                | Trade Operations Analyst         |
| AS-05 | Compare confirmation details            | Trade Operations Analyst         |
| AS-06 | Investigate detected discrepancies      | Trade Operations Analyst         |
| AS-07 | Request and record approved corrections | Authorised approver / Operations |
| AS-08 | Prepare reporting data                  | Regulatory Reporting Analyst     |
| AS-09 | Reconcile records and outcomes          | Trade Operations Analyst         |
| AS-10 | Compile operational status reports      | Operations Manager               |

### 9.3 Business Pain Points

**BN-001 — Reduce Re-keying Defects**

Manual transfer of trade details introduces a risk of
incorrect or inconsistent values.

**BN-002 — Detect Errors Earlier**

Insufficient early validation can allow trade-data
discrepancies to progress into downstream processing.

**BN-003 — Improve Exception Resolution**

Manual investigation and fragmented exception tracking
can increase operational effort.

**BN-004 — Preserve Trade Amendment History**

Original values, amended values and approval decisions
must remain traceable.

**BN-005 — Improve Reporting Data Quality**

Reporting preparation requires validated, complete
and consistent trade information.

**BN-006 — Improve Operational Visibility**

Operations management needs reliable metrics for
processing efficiency, validation outcomes and exceptions.

### 9.4 T-1001 AS-IS Scenario

Trade ID: T-1001
Product: GBP Interest Rate Swap
Tenor: 10 Years

Intended Notional: GBP 10,000,000
Captured Notional: GBP 100,000,000

The incorrect captured notional is a valid positive
numeric value and may pass basic format validation.

Without timely comparison against an independent
confirmation, the discrepancy may remain undetected.

The scenario demonstrates the need for:

- Early confirmation matching
- Exception tracking
- Authorised amendments
- Preserved version history
- Reporting controls
- Operational traceability

### 9.5 Business Impact

Potential impacts include:

- Increased manual processing effort
- Delayed exception resolution
- Additional reconciliation workload
- Reduced straight-through processing
- Reporting preparation delays
- Limited management visibility

These impacts are qualitative assumptions.
Quantitative improvements will only be claimed
when supported by project test results.

### 9.6 Improvement Opportunities

The proposed solution should introduce:

1. Standardised trade data ingestion.
2. Automated validation and confirmation matching.
3. Structured exception management.
4. Human-approved trade amendments.
5. Immutable trade-version history.
6. Controlled simulated reporting.
7. Reconciled operational KPI dashboards.

## 10. Business Needs & Pain Point Analysis

### 10.1 Purpose

This section translates the problems identified in the
AS-IS trade-processing workflow into prioritised
business needs.

Each business need is assigned a unique identifier
to support requirements traceability across the project.

### 10.2 Business Needs Register

| Need ID | Business Need                  | Priority | Stakeholder          |
| ------- | ------------------------------ | -------- | -------------------- |
| BN-001  | Reduce re-keying defects       | Must     | Trade Operations     |
| BN-002  | Detect trade errors earlier    | Must     | Trade Operations     |
| BN-003  | Improve exception resolution   | Must     | Trade Operations     |
| BN-004  | Preserve amendment history     | Must     | Risk / Compliance    |
| BN-005  | Improve reporting data quality | Must     | Regulatory Reporting |
| BN-006  | Improve operational visibility | Should   | Operations Manager   |

### 10.3 Detailed Business Needs

#### BN-001 — Reduce Re-keying Defects

**Current Problem:**
Trade information may be manually transferred between
operational systems, increasing the risk of incorrect
or inconsistent values.

**Business Need:**
Reduce manual data transfer and identify discrepancies
between captured and confirmed trade information.

**Expected Outcome:**
Fewer undetected trade-data discrepancies.

**Measurement:**
Number and percentage of trades with detected
re-keying-related defects.

#### BN-002 — Detect Trade Errors Earlier

**Current Problem:**
Trade discrepancies may only be identified during
later confirmation or reporting activities.

**Business Need:**
Introduce earlier validation and confirmation-matching
controls before downstream reporting.

**Expected Outcome:**
More defects identified before reporting preparation.

**Measurement:**
Percentage of known seeded defects detected
before simulated reporting.

#### BN-003 — Improve Exception Resolution

**Current Problem:**
Manual investigation and fragmented tracking may
delay the resolution of trade exceptions.

**Business Need:**
Provide clear exception ownership, status tracking
and a controlled resolution process.

**Expected Outcome:**
Improved traceability and resolution efficiency.

**Measurement:**
Exception resolution time and percentage of
exceptions resolved.

#### BN-004 — Preserve Trade Amendment History

**Current Problem:**
Original trade values, correction decisions and
amendment history may be difficult to reconstruct.

**Business Need:**
Preserve original and amended trade versions,
including approval and audit information.

**Expected Outcome:**
Complete traceability of trade corrections.

**Measurement:**
Percentage of amended trades with complete
version and approval history.

#### BN-005 — Improve Reporting Data Quality

**Current Problem:**
Incorrect or incomplete trade information may
reach downstream reporting preparation.

**Business Need:**
Validate required reporting fields and reconcile
simulated reporting outcomes.

**Expected Outcome:**
Fewer reporting-data exceptions and clearer
correction and resubmission evidence.

**Measurement:**
Simulated reporting rejection rate and
reporting-field completeness.

#### BN-006 — Improve Operational Visibility

**Current Problem:**
Operational status and exception information may
be fragmented across manual reports.

**Business Need:**
Provide consolidated dashboards showing trade
volumes, processing outcomes and exceptions.

**Expected Outcome:**
Better operational monitoring and prioritisation.

**Measurement:**
Dashboard reconciliation accuracy, trade volumes,
straight-through processing rate and latency.

### 10.4 Business Need Prioritisation

The MoSCoW method is used to classify needs.

**Must Have:**
BN-001, BN-002, BN-003, BN-004, BN-005

**Should Have:**
BN-006

These are initial priorities and may be refined
during Phase 2 requirements design.

### 10.5 Business Need Traceability

Each business need will be linked to:

- Functional requirements
- User stories
- Relevant data fields
- Validation or processing controls
- Operational KPIs
- Acceptance tests
- Evidence of implementation

The Requirements Traceability Matrix (RTM)
will be developed in Phase 2 and completed
during integration testing.

### 10.6 Measurement Principles

All operational metrics must define:

1. Numerator, where applicable.
2. Denominator, where applicable.
3. Measurement grain.
4. Reporting period.
5. Data source.
6. Handling of missing or invalid values.

The detailed KPI Dictionary will be defined
in Step 1.9.

No quantitative improvement will be claimed
without measured evidence.

## 11. Business Requirements Document (BRD)

### 11.1 Purpose

This Business Requirements Document defines the business
capabilities and outcomes required by NorthBridge Markets
to improve the OTC trade-processing lifecycle.

The BRD establishes traceability between business needs,
expected operational outcomes and acceptance criteria.

Detailed functional and non-functional requirements
will be specified during Phase 2.

### 11.2 Business Problem Statement

The current fictional AS-IS workflow involves manual
re-keying, fragmented validation and exception handling,
and limited operational visibility.

These conditions can allow trade-data discrepancies to
progress into downstream processing, creating additional
investigation, reconciliation and reporting effort.

NorthBridge Markets requires a controlled and traceable
trade-processing workflow that detects errors earlier,
supports authorised corrections and provides reliable
operational information.

### 11.3 Business Requirements Register

| ID     | Requirement                                                          | Need ID | Priority |
| ------ | -------------------------------------------------------------------- | ------- | -------- |
| BR-001 | Improve trade capture accuracy and discrepancy identification        | BN-001  | Must     |
| BR-002 | Detect trade validation and confirmation exceptions before reporting | BN-002  | Must     |
| BR-003 | Support accountable exception investigation and resolution           | BN-003  | Must     |
| BR-004 | Preserve trade versions, amendments and approval evidence            | BN-004  | Must     |
| BR-005 | Validate and reconcile simulated reporting information               | BN-005  | Must     |
| BR-006 | Provide operational KPIs and exception visibility                    | BN-006  | Should   |

### 11.4 Detailed Business Requirements

#### BR-001 — Trade Data Accuracy

**Business Requirement:**
NorthBridge Markets must be able to identify discrepancies
between captured trade details and independently confirmed
trade economics.

**Business Rationale:**
Reduce the risk of undetected manual re-keying errors.

**Business Acceptance Criteria:**

- Known seeded notional discrepancies are identified.
- Each detected discrepancy is associated with a trade ID.
- Original captured values remain available for review.

#### BR-002 — Early Trade Validation

**Business Requirement:**
Trades must undergo defined validation and confirmation
checks before proceeding to simulated reporting.

**Business Rationale:**
Prevent known invalid or mismatched records from
progressing without appropriate exception handling.

**Business Acceptance Criteria:**

- Defined mandatory-field and business-rule checks run.
- Known seeded defects generate expected validation results.
- Trades with unresolved blocking exceptions are held.

#### BR-003 — Exception Management

**Business Requirement:**
Operational exceptions must be identifiable, assigned,
investigated and resolved through a controlled process.

**Business Rationale:**
Improve accountability and reduce fragmented investigation.

**Business Acceptance Criteria:**

- Each exception has an identifiable trade and reason.
- Exception ownership and status are recorded.
- Resolution outcomes can be reviewed.

#### BR-004 — Trade Amendment Auditability

**Business Requirement:**
Trade corrections must preserve the original record,
corrected version and authorised approval evidence.

**Business Rationale:**
Ensure amendments are traceable and auditable.

**Business Acceptance Criteria:**

- Original and amended trade versions remain available.
- Amendment approval is recorded.
- Version history identifies the change and its timing.
- T-1001 retains its original and corrected notional.

#### BR-005 — Reporting Data Quality

**Business Requirement:**
Reporting information must be validated and reconciled
against the applicable demonstration reporting rules.

**Business Rationale:**
Reduce reporting-data exceptions and improve
investigation of simulated reporting outcomes.

**Business Acceptance Criteria:**

- Required reporting fields are mapped.
- Reporting validation outcomes are recorded.
- Simulated reporting exceptions are traceable.
- Corrected records can be revalidated and resubmitted
  within the demonstration workflow.

#### BR-006 — Operational Performance Visibility

**Business Requirement:**
Operations management should have access to consolidated
trade-processing and exception-performance information.

**Business Rationale:**
Support monitoring, prioritisation and process improvement.

**Business Acceptance Criteria:**

- Trade volumes and exception counts are available.
- STP and validation failure rates are calculated.
- Simulated reporting outcomes are visible.
- Dashboard totals reconcile with underlying records.

### 11.5 Business Rules and Constraints

The following business constraints apply:

1. Only synthetic trade data will be used.
2. Initial product scope is GBP interest-rate swaps.
3. Original trade records must not be overwritten.
4. Trade amendments require authorised human approval.
5. Unresolved blocking exceptions prevent simulated
   reporting progression.
6. Simulated reporting must not be represented as an
   actual regulatory submission.
7. Operational KPIs must use documented definitions.
8. Predictive scores must not replace validation controls
   or human approval.

### 11.6 Dependencies and Assumptions

- Stakeholder roles are representative assumptions.
- The independent confirmation fixture provides the
  intended trade economics for reconciliation.
- Technical architecture will be finalised in Phase 2.
- Data validation controls will be implemented in Phase 3.
- Analytics and reporting will be implemented in Phase 4.
- Predictive intelligence will be developed in Phase 5.
- AI-assisted investigation will be implemented in Phase 6.

### 11.7 BRD Acceptance

The BRD baseline is ready for Phase 2 when:

- All six business needs map to business requirements.
- Every Must requirement has testable business criteria.
- Scope and exclusions are documented.
- T-1001 is represented in the requirements.
- Business assumptions are clearly identified.

## 12. Product Requirements Document (PRD)

### 12.1 Product Overview

NorthBridge TradeFlow is a proposed integrated trade-processing
and operational intelligence solution for the fictional
NorthBridge Markets organisation.

The product will support the lifecycle of synthetic GBP
interest-rate swaps through validation, exception management,
human-approved amendment, simulated reporting, analytics,
predictive risk scoring and AI-assisted investigation.

### 12.2 Target Users

The primary users are:

- Trade Operations Analyst
- Front Office Trader
- Middle Office / Risk Analyst
- Compliance & Regulatory Reporting Analyst
- Operations Manager

The Data Engineering Team supports the underlying data
processing, controls and operational reliability.

### 12.3 Product Requirements

#### PR-001 — Trade Information Access

Users should be able to:

- Identify trades by unique trade ID.
- View captured trade economics.
- Inspect trade status and version.
- Review relevant processing timestamps.

Linked Requirement: BR-001

#### PR-002 — Trade Validation Visibility

Users should be able to:

- Review trade validation outcomes.
- Identify failed validation rules.
- Compare captured and confirmed trade details.
- Understand why a trade was flagged.
- Identify unresolved blocking exceptions.

Linked Requirement: BR-002

#### PR-003 — Exception Investigation

Trade Operations users should be able to:

- View trade exceptions.
- Identify the exception reason and status.
- Review available supporting evidence.
- Record or inspect exception ownership.
- Track investigation and resolution outcomes.

Linked Requirement: BR-003

#### PR-004 — Controlled Trade Amendment

Authorised users should be able to:

- Request a trade correction.
- Review the proposed amendment.
- Approve or reject the correction.
- Inspect the original and amended values.
- Review amendment history and timestamps.

Trade amendments must not occur without authorised approval.

Linked Requirement: BR-004

#### PR-005 — Simulated Reporting

Reporting users should be able to:

- Review reporting-field validation results.
- Identify missing or inconsistent reporting data.
- View simulated submission status.
- Investigate simulated rejection reasons.
- Review correction and resubmission history.

No external regulatory submission is included.

Linked Requirement: BR-005

#### PR-006 — Operational Analytics

Operations managers should be able to monitor:

- Trade volumes
- Straight-through processing rate
- Validation failure rate
- Exception counts and status
- Simulated reporting rejection rate
- Processing latency

Dashboard metrics must reconcile with underlying data.

Linked Requirement: BR-006

#### PR-007 — Predictive Risk Intelligence

Relevant users should be able to:

- Obtain a computed rejection-risk score.
- View the associated model version.
- Understand the risk classification threshold.
- Review available model explanations.
- Distinguish predictions from observed validation facts.

Predictions must not automatically approve, amend
or submit trades.

Linked Requirements: BR-002, BR-003

#### PR-008 — AI Operations Assistant

Trade Operations users should be able to:

- Ask questions about a specific trade.
- Retrieve relevant trade and validation information.
- Review applicable knowledge and rule references.
- Receive evidence-based explanations.
- Identify when information is unavailable.

The assistant must not autonomously modify trade
records or submit reporting information.

Linked Requirements: BR-003, BR-006

### 12.4 Core User Journey — T-1001

1. A user accesses trade T-1001.
2. The captured notional is GBP 100,000,000.
3. Independent confirmation indicates GBP 10,000,000.
4. Validation identifies DEMO_NOTIONAL_MISMATCH.
5. The trade is flagged for investigation.
6. An authorised user reviews the proposed correction.
7. Approval is recorded before amendment.
8. Trade version 2 retains the corrected notional.
9. The original version remains available.
10. The corrected trade is revalidated.
11. A simulated reporting outcome is generated.
12. Operational analytics show the exception and resolution.
13. A prediction service provides a computed risk score.
14. The AI assistant explains the trade using cited evidence.

### 12.5 Product Boundaries

The initial release will not support:

- Live trade execution
- Real client data
- External regulatory submission
- Autonomous trade amendments
- Autonomous regulatory reporting
- Production certification

### 12.6 Product Success Criteria

The product will meet its intended objectives when:

1. Trade information is accessible and traceable.
2. Known seeded defects are correctly identified.
3. Blocking exceptions prevent reporting progression.
4. Amendment approval and history are preserved.
5. Simulated reporting outcomes are reproducible.
6. Operational KPIs reconcile with source records.
7. Predictive outputs include model version and evidence.
8. AI explanations cite relevant retrieved information.
9. Core user journeys pass documented acceptance tests.

### 12.7 Delivery Dependencies

- Phase 2: Solution design and technical requirements
- Phase 3: Data foundation and validation
- Phase 4: Analytics and simulated reporting intelligence
- Phase 5: Predictive modelling
- Phase 6: Model API and AI operations assistant
- Phase 7: Integration testing and deployment evidence

### 12.8 PRD Status

The PRD defines intended capabilities.
It does not imply that these features are implemented.

## 13. KPI & Metric Dictionary

### 13.1 Purpose

The KPI Dictionary establishes standard definitions for
measuring operational efficiency, data quality, exception
management and simulated reporting performance.

All KPI calculations must use consistent business rules,
measurement grains and reporting periods.

### 13.2 KPI Definitions

#### KPI-001 — Straight-Through Processing Rate

Business Objective:
Measure the percentage of trades processed without
manual intervention or amendment.

Formula:
STP Rate (%) =
(STP Eligible Trades / Total Eligible Trades) × 100

Numerator:
Distinct eligible trade IDs completing the defined
workflow without manual intervention, exception
resolution or amendment.

Denominator:
Distinct trade IDs eligible for the completed workflow.

Grain:
One logical trade ID, not one trade version.

Unit: Percentage

Linked Business Need: BN-001, BN-003

#### KPI-002 — Validation Failure Rate

Business Objective:
Measure how frequently trades fail validation.

Formula:
Validation Failure Rate (%) =
(Trades with Validation Failures / Validated Trades) × 100

Numerator:
Distinct trade IDs with at least one failed validation
in the selected reporting period.

Denominator:
Distinct trade IDs validated in the same period.

Grain:
One logical trade ID per reporting period.

Unit: Percentage

Linked Business Need: BN-002

Note:
This is a period-based failure incidence metric.
A separate current-state metric may be created to
show unresolved validation failures.

#### KPI-003 — Exception Resolution Rate

Business Objective:
Measure the percentage of recorded exceptions resolved.

Formula:
Exception Resolution Rate (%) =
(Resolved Exceptions / Total Exceptions) × 100

Numerator:
Distinct exception IDs marked Resolved within the
defined exception cohort.

Denominator:
Distinct exception IDs in that cohort.

Grain:
One exception ID.

Unit: Percentage

Linked Business Need: BN-003

#### KPI-004 — Average Exception Resolution Time

Business Objective:
Measure how long exception resolution takes.

Formula:
Average Resolution Time =
SUM(Resolved Timestamp - Created Timestamp)
/
Number of Resolved Exceptions

Numerator:
Total resolution duration for resolved exceptions.

Denominator:
Number of resolved exception IDs.

Grain:
One resolved exception ID.

Unit: Hours

Linked Business Need: BN-003

#### KPI-005 — Simulated Reporting Rejection Rate

Business Objective:
Measure the proportion of simulated reporting
attempts receiving a rejected outcome.

Formula:
Simulated Rejection Rate (%) =
(Rejected Simulated Attempts / Total Simulated Attempts)
× 100

Numerator:
Number of simulated reporting attempts with a
Rejected outcome.

Denominator:
Total simulated reporting attempts with a
final Accepted or Rejected outcome.

Grain:
One simulated submission attempt ID.

Unit: Percentage

Linked Business Need: BN-005

Note:
This is not a real regulatory rejection rate.
Multiple attempts for one trade are counted separately.

#### KPI-006 — Trade Processing Latency

Business Objective:
Measure processing time from trade capture to
the selected processing outcome.

Formula:
Processing Latency =
Outcome Timestamp - Capture Timestamp

Numerator:
Total elapsed processing duration across completed trades.

Denominator:
Number of completed logical trades.

Grain:
One logical trade ID.

Unit: Seconds

Linked Business Need: BN-002, BN-006

Note:
Report average latency and optionally P95 latency.
The selected outcome must be consistent across trades.

#### KPI-007 — Amendment Rate

Business Objective:
Measure the proportion of trades requiring amendment.

Formula:
Amendment Rate (%) =
(Amended Trades / Total Eligible Trades) × 100

Numerator:
Distinct trade IDs with at least one approved amendment.

Denominator:
Distinct trade IDs in the selected trade cohort.

Grain:
One logical trade ID.

Unit: Percentage

Linked Business Need: BN-004

#### KPI-008 — Reporting Field Completeness

Business Objective:
Measure completeness of mandatory simulated
reporting fields.

Formula:
Reporting Completeness (%) =
(Populated Required Field Instances /
Total Required Field Instances) × 100

Numerator:
Number of required field instances containing
non-null, non-blank values.

Denominator:
Number of applicable required field instances.

Grain:
One required field per reporting record.

Unit: Percentage

Linked Business Need: BN-005

Note:
Completeness does not guarantee correctness.
Conditional field applicability must be considered.

### 13.3 Common Calculation Rules

1. Trade IDs identify logical trades.
2. Trade versions identify historical records.
3. Current-trade KPIs must not double-count versions.
4. Exception KPIs use unique exception IDs.
5. Reporting attempt KPIs use submission attempt IDs.
6. Percentage KPIs must handle zero denominators.
7. Missing timestamps must not be treated as zero duration.
8. Reporting periods and timezone conventions must be
   documented.
9. Synthetic demonstration results must not be presented
   as actual production performance.

### 13.4 Data Sources

The planned KPI calculations will use:

- Trade records and version history
- Validation outcomes
- Exception records
- Amendment and approval events
- Simulated reporting outcomes
- Processing timestamps

The detailed data model will be defined in Phase 2
and implemented in Phase 3.

### 13.5 KPI Validation

During Phase 4:

- SQL will calculate the reference KPI values.
- Power BI measures will be reconciled against SQL.
- Filters and denominators must be consistent.
- Amended trade versions must not inflate trade counts.
- T-1001 must appear correctly in exception analysis.

Status: Draft — Pending Data Model Confirmation

## 14. Trade Data Dictionary

### 14.1 Purpose

Define the standard data contract for synthetic GBP
interest-rate swap transactions used throughout
NorthBridge TradeFlow.

The detailed field-level dictionary is maintained
in data/phase_1/Data_Dictionary.xlsx.

### 14.2 Data Contract

Dataset: sample_trades.csv
Entity: Trade Record
Product: GBP Interest Rate Swap
Field Count: 20
Primary Key: (trade_id, trade_version)
Data Classification: Synthetic

### 14.3 Data Standards

- Column names use snake_case.
- Dates use ISO 8601 format: YYYY-MM-DD.
- Timestamps use UTC ISO 8601 format.
- Currency uses ISO 4217 codes.
- Notional amounts are stored in GBP.
- Fixed rates use decimal representation.
- Trade versions are positive integers.
- Missing optional values use null/blank.
- Historical trade versions must not be overwritten.

### 14.4 Versioning

A logical trade is identified by trade_id.

Each historical record is identified by:
(trade_id, trade_version).

For T-1001:

Version 1: GBP 100,000,000 — original captured value.
Version 2: GBP 10,000,000 — approved corrected value.

Both versions must remain traceable.

### 14.5 Validation

The dataset will be checked for:

- Mandatory-field completeness
- Correct data types
- Valid business values
- Positive notional amounts
- Date consistency
- Unique composite keys
- Valid trade-version sequencing

### 14.6 Confirmation Matching

The intended trade economics will be stored in a
separate independent confirmation fixture.

For T-1001:

Captured Notional: GBP 100,000,000
Confirmed Notional: GBP 10,000,000

Expected Demo Rule:
DEMO_NOTIONAL_MISMATCH

A valid numeric amount does not necessarily mean
the captured economic terms are correct.

### 14.7 Change Control

The Phase 1 schema is a proposed baseline.

It will be reviewed and frozen during Phase 2.
Any later schema changes must be documented.

## 15. Synthetic Data and Seeded Defects

### 15.1 Data Fixtures

The project uses a reproducible synthetic dataset
containing 50 GBP interest-rate swap trades.

The original baseline is preserved in sample_trades.csv.

Ten intentionally defective records are maintained
separately in seeded_errors.csv.

Expected validation outcomes are documented in
seeded_error_manifest.csv.

Independent reference economics are maintained in
independent_confirmations.csv.

### 15.2 T-1001 Demonstration Scenario

Trade ID: T-1001
Trade Version: 1
Product: GBP Interest Rate Swap
Tenor: 10 years
Captured Notional: GBP 100,000,000
Confirmed Notional: GBP 10,000,000

Expected Rule: DEMO_NOTIONAL_MISMATCH

The mismatch is identified by comparing captured
and confirmed trade economics.

The original captured record must be retained.

A corrected version may only be created following
authorised human approval in the later workflow.

### 15.3 Data Quality Testing

Seeded defects cover:

- Missing mandatory information
- Invalid numeric values
- Invalid business values
- Date inconsistencies
- Cross-record confirmation mismatches

Each seeded defect has a documented expected rule.

### 15.4 Data Governance

All records are synthetic.

No real counterparty or client information is used.

The demonstration does not perform real regulatory
reporting or live trade processing.

Status: Fixtures Prepared — Pending Validation Testing
