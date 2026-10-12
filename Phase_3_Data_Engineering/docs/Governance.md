# NorthBridge TradeFlow — Data Governance

## 1. Purpose

This document describes the data governance, security, auditability and operational controls implemented in Phase 3 of NorthBridge TradeFlow.

The project demonstrates how synthetic OTC interest-rate swap data can be processed through a controlled, traceable and reproducible data engineering pipeline.

## 2. Governance Objectives

The governance approach focuses on:

- **Data integrity:** Prevent invalid records from entering curated datasets.
- **Traceability:** Maintain batch identifiers, validation metadata and processing records.
- **Access security:** Use authenticated connections to cloud services.
- **Auditability:** Record validation and ingestion outcomes.
- **Reproducibility:** Support deterministic batch processing and safe reruns.
- **Data separation:** Distinguish raw, curated and quarantined datasets.

## 3. Data Classification

| Data Category                          | Classification           | Handling                                             |
| -------------------------------------- | ------------------------ | ---------------------------------------------------- |
| Synthetic OTC trade records            | Synthetic project data   | Used for pipeline development and analytics          |
| Independent confirmations              | Synthetic project data   | Used for validation and reconciliation               |
| Curated trade datasets                 | Validated synthetic data | Used for Snowflake ingestion and dbt transformations |
| Quarantined records                    | Rejected synthetic data  | Preserved for investigation                          |
| Validation and ingestion audit records | Operational metadata     | Retained for pipeline traceability                   |
| Azure and Snowflake credentials        | Sensitive configuration  | Excluded from public GitHub                          |

**Important:** This portfolio project uses synthetic data. It does not claim to process real customer trading records or production financial information.

## 4. Data Ownership and Responsibilities

For this portfolio implementation, development, administration and validation are performed by the project developer.

In a production environment, responsibilities would typically be separated between:

- Data owners responsible for business definitions and data usage.
- Data engineers responsible for ingestion and transformations.
- Data stewards responsible for data-quality oversight.
- Security administrators responsible for access management.
- Risk and compliance teams responsible for regulatory requirements.

These production roles represent a proposed governance structure, not an organizational process implemented in the portfolio.

## 5. Security and Access Controls

### Azure Storage

The project uses Azure Data Lake Storage Gen2 as the cloud data foundation.

The Python validation pipeline supports Azure credential-based authentication and a local storage mode for working with backed-up project data.

### Snowflake Authentication

Snowflake ingestion uses RSA private-key authentication.

The private key is stored outside the Git repository, and its passphrase is requested interactively.

Snowflake roles and privileges govern access to warehouse resources.

### Secrets Management

The repository uses `.gitignore` rules to exclude sensitive local configuration files, including:

- `.env` files
- Private-key files
- Local Azure backups
- Runtime logs
- Local credential configuration

Gitleaks is used during repository security review to identify potentially exposed secrets.

**Limitation:** Git ignore rules and automated secret scans reduce exposure risk but cannot guarantee that all credentials are protected. Access permissions and credential rotation remain important operational controls.

## 6. Data Lineage

The logical data lineage is:

```text
Synthetic Trade Sources
          |
          v
Azure ADLS Gen2 — Raw Layer
          |
          v
Python Validation Pipeline
          |
          +----> Quarantine (BLOCK)
          |
          v
Curated Validated Trades (PASS)
          |
          v
Snowflake CURATED.TRADES_VALIDATED
          |
          v
dbt Staging Models
          |
          v
dbt Intermediate Models
          |
          v
dbt Analytics Marts
```

Batch identifiers, validation run identifiers, source checksums and completion metadata provide traceability between processing stages.

## 7. Data Quality Governance

Trade-level validation determines whether records are accepted or blocked.

The implementation includes:

- Required-field and validation-rule checks.
- Independent confirmation comparisons.
- Source integrity checks using SHA-256.
- Separation of curated and quarantined records.
- Batch metadata verification.
- dbt staging-level data-quality tests.

The verified test batch produced:

| Metric               |       Result |
| -------------------- | -----------: |
| Source records       |           50 |
| Accepted records     |           49 |
| Quarantined records  |            1 |
| Acceptance rate      |          98% |
| Manifest tests       | 10/10 passed |
| dbt build operations |    13 passed |

Further validation details are documented in `Data_Quality_Plan.md`.

## 8. Audit Logging and Traceability

The validation pipeline produces metadata and audit outputs describing processing outcomes.

The ingestion pipeline records execution events such as:

- `STARTED`
- `SUCCESS`
- `SKIPPED`
- `FAILED`

Completion markers indicate successfully completed validation batches.

These controls support investigation of processing outcomes and help distinguish successful execution from skipped or failed operations.

## 9. Idempotency and Duplicate Prevention

The implementation uses deterministic batch identification and verification of previously processed data.

Key controls include:

1. Detecting existing validation batch outputs.
2. Preventing unintentional overwriting of completed outputs.
3. Checking existing Snowflake records by validation run identifier.
4. Skipping ingestion when the expected complete batch already exists.
5. Rejecting unexpected partial-batch conditions.

This reduces the risk of duplicate records when the pipeline is rerun.

## 10. Orchestration and Failure Handling

The Python orchestrator executes:

1. Trade validation.
2. Snowflake ingestion.
3. dbt transformations and tests.

Each stage must complete successfully before the next stage executes.

If a stage fails, the orchestrator stops and reports a failure rather than proceeding with potentially incomplete data.

The verified execution completed with:

`PIPELINE STATUS: SUCCESS`

## 11. Data Retention and Recovery

The project maintains local backups of Azure data to support development continuity when cloud resources become unavailable.

Backup data is excluded from the public Git repository.

**Current limitation:** Automated backup scheduling, formal retention periods, disaster-recovery objectives and tested production restoration procedures are not part of this Phase 3 implementation.

These would require defined policies and operational testing in a production deployment.

## 12. Regulatory Considerations

OTC derivatives operations may be subject to regulatory reporting, recordkeeping, privacy and operational-resilience requirements depending on the jurisdiction and business context.

NorthBridge TradeFlow is a synthetic educational portfolio project and does not claim compliance certification or implementation of a full regulatory reporting framework.

Formal regulatory mappings, retention requirements, surveillance controls and compliance approval workflows are outside the current Phase 3 scope.

## 13. Future Governance Enhancements

Potential future improvements include:

- Centralized secrets management using a managed vault.
- Automated access reviews and periodic credential rotation.
- Centralized audit monitoring and alerting.
- Defined retention and deletion policies.
- Automated data lineage cataloguing.
- Formal business data ownership and approval processes.
- Recovery testing and documented service-level objectives.

These are proposed enhancements rather than completed features.

## 14. Governance Summary

Phase 3 demonstrates practical governance controls through authenticated cloud access, data validation, quarantine separation, reproducible processing, audit metadata, duplicate protection and automated testing.

The implementation provides a foundation for extending NorthBridge TradeFlow into a more comprehensive trade operations and analytics platform.
