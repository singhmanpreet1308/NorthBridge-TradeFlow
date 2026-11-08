
# NorthBridge TradeFlow — Apache Airflow Orchestration

## Overview

Apache Airflow orchestrates the NorthBridge TradeFlow
trade validation pipeline.

The workflow connects to Azure Data Lake Storage Gen2,
validates OTC interest-rate swap trade data, performs
independent confirmation reconciliation, and verifies
curated, quarantine, and audit outputs.

## Technology Stack

- Apache Airflow 3.1.0
- Docker Desktop and Docker Compose
- PostgreSQL 16
- Python 3.12
- Azure Data Lake Storage Gen2
- Microsoft Entra ID service principal
- Azure SDK for Python
- Pytest

## Architecture

Raw Trade Data (Azure ADLS Gen2)
           |
           v
Apache Airflow Scheduler
           |
           v
northbridge_trade_validation DAG
           |
           v
validate.py
           |
           +-- Schema validation
           +-- Data-quality checks
           +-- Confirmation reconciliation
           +-- Seeded defect verification
           +-- Curated/quarantine separation
           +-- SHA-256 integrity verification
           |
           v
Azure ADLS Gen2 Outputs
           |
           +-- curated/trades/
           +-- quarantine/trades/
           +-- curated/audit/

## Docker Services

| Service               | Purpose                            |
| --------------------- | ---------------------------------- |
| postgres              | Airflow metadata database          |
| airflow-init          | Database initialization/migrations |
| airflow-api-server    | Airflow web interface and API      |
| airflow-scheduler     | Task scheduling                    |
| airflow-dag-processor | DAG discovery and parsing          |

Executor: LocalExecutor

## Azure Authentication

The pipeline supports two authentication methods:

- Local Windows development: AzureCliCredential
- Docker/Airflow: EnvironmentCredential

Required environment variables:

AZURE_TENANT_ID
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET

Credentials are loaded from the local .env file.

Never commit .env files or client secrets to Git.

The Airflow service principal requires
Storage Blob Data Contributor permissions.

Azure Storage firewall rules must also permit
the environment's outbound network traffic.

## Production DAG

DAG ID: northbridge_trade_validation

Source:
dags/northbridge_validation_dag.py

Pipeline:
../pipeline/validate.py

Execution: Manual trigger

Maximum active DAG runs: 1

Failure handling:

- Retries: 2
- Retry delay: 2 minutes
- Task execution timeout: 15 minutes

The DAG executes the existing validation pipeline
through a Python subprocess.

A non-zero process exit code causes task failure.

## Validated Results

| Control                  | Verified result  |
| ------------------------ | ---------------- |
| Baseline trades          | 50               |
| Curated trades           | 49               |
| Quarantined trades       | 1                |
| Seeded defect tests      | 10/10 passed     |
| Regression tests         | 20/20 passed     |
| Existing batch handling  | Verified/skipped |
| Output checksums         | Verified         |
| Production DAG execution | Successful       |

## Batch Idempotency

The validation pipeline derives a stable batch ID
from source checksums and validation policy version.

Completed batches are verified rather than
overwritten.

A completion marker (_SUCCESS.json) indicates
successful batch publication.

SHA-256 checksums support output integrity checks.

## Reliability Testing

A temporary retry test DAG was created to verify
Airflow's retry mechanism.

Test results:

- Initial attempt failed intentionally.
- Two automatic retries were executed.
- Three total attempts were confirmed.
- Final failure was expected.

The temporary DAG and its metadata were removed
after testing.

The production DAG's retry and timeout settings
were also verified through Airflow configuration
inspection.

## Running the Environment

From the airflow directory:

    docker compose up -d

Airflow UI:

    http://localhost:8080

Trigger the northbridge_trade_validation DAG manually
from the Airflow interface.

Check the run_validation task logs to review
validation results.

## Useful Commands

Validate Docker Compose configuration:

    docker compose config --quiet

View running containers:

    docker compose ps

Check DAG import errors:

    docker compose exec airflow-scheduler airflow dags list-import-errors

List registered DAGs:

    docker compose exec airflow-scheduler airflow dags list

Run regression tests from the repository root:

    python -m pytest Phase_3_Data_Engineering/pipeline/test_validate.py -v

## Implementation Status

Airflow orchestration: Completed

Azure ADLS Gen2 integration: Verified

Trade validation DAG: Operational

Retry mechanism: Tested

Data-quality controls: Verified

Batch idempotency: Verified

Regression testing: 20/20 passed
