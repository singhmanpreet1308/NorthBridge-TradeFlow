# NorthBridge TradeFlow — Data Model

## 1. Overview

NorthBridge TradeFlow is a synthetic OTC interest-rate swaps data engineering project.

The data model supports trade validation, version tracking, portfolio reporting, counterparty exposure analysis and maturity analysis.

The architecture follows a layered data processing approach:

Raw Data → Validated Curated Data → Snowflake → dbt Transformations → Analytics Marts

## 2. Data Architecture

### Raw Layer — Azure Data Lake Storage Gen2

Stores synthetic trade records, independent confirmations and source datasets.

Example source paths:

- `raw/trades/sample_trades.csv`
- `raw/confirmations/independent_confirmations.csv`

### Curated Layer — Validated Trade Data

Contains records that pass validation checks.

Output:

`curated/trades/{batch_id}/validated_trades.csv`

Records failing validation are separated into a quarantine dataset.

### Snowflake Warehouse

Database: `NORTHBRIDGE_TRADEFLOW`

Primary ingestion table:

`CURATED.TRADES_VALIDATED`

The table contains 26 columns, including trade attributes and validation metadata.

For the verified batch:

- 50 source trades
- 49 validated records
- 1 quarantined record

## 3. dbt Transformation Layers

### Staging

**`stg_trades_validated`**

Standardizes the Snowflake curated trade data for downstream transformations.

### Intermediate

**`int_trade_enriched`**

Derives trade attributes, including tenor and remaining maturity.

**`int_current_trades`**

Identifies the latest available version of each trade.

**`int_trade_version_history`**

Maintains a transformation-level view of trade versions for historical analysis.

### Analytics Marts

**`mart_counterparty_exposure`**

Provides counterparty-level portfolio exposure analysis.

**`mart_trade_portfolio_summary`**

Produces aggregated trade portfolio metrics.

**`mart_trade_maturity_distribution`**

Supports maturity-bucket reporting.

**`mart_trade_validation_summary`**

Summarizes batch validation results using the validation audit seed.

## 4. Logical Data Flow

```text
Synthetic Trade Sources
        |
        v
Azure ADLS Gen2 — Raw
        |
        v
Python Validation Pipeline
        |
        +------> Quarantine (Failed Records)
        |
        v
Curated Validated Trades
        |
        v
Snowflake CURATED.TRADES_VALIDATED
        |
        v
dbt Staging
        |
        v
dbt Intermediate Models
        |
        v
dbt Analytics Marts
```

## 5. Data Integrity and Versioning

The data pipeline implements:

- Trade identifier uniqueness checks.
- Validation-status checks.
- Validation run and batch metadata verification.
- Source checksum verification.
- Duplicate batch ingestion prevention.
- Latest-trade-version selection.
- Trade version history transformations.

## 6. Model Validation

The completed dbt build executed:

- 8 custom SQL models.
- 1 audit seed.
- 4 data-quality tests.

**Result: 13 successful operations, 0 failures.**

## 7. Design Considerations

- Layered architecture separates ingestion from analytical transformations.
- Deterministic batch identifiers support repeatable processing.
- Curated and quarantined outputs separate accepted and rejected trades.
- dbt enables modular, maintainable SQL transformations.
- Analytics marts provide reusable datasets for reporting and future downstream applications.

## 8. Scope

This document describes the logical data architecture and transformation models implemented in Phase 3.

Detailed column definitions, physical Snowflake DDL and exact business metric calculations should be maintained alongside the corresponding SQL and dbt source files.
