# T-1001 Golden Thread — Run Report

- **Overall:** PASS
- **Run at (UTC):** 2026-11-10T15:25:25.726909+00:00
- **Total runtime:** 4.116 s
- **LLM mode:** TemplateLLM (offline stub)
- **Environment:** Python 3.12.15 · Windows-11-10.0.26300-SP0

| Stage | Name | Component | Status | Seconds |
| --- | --- | --- | --- | --- |
| GT-01 | Original capture | Phase 1 fixtures | PASS | 0.048 |
| GT-02 | Validation, exception and publication | Phase 3 pipeline.validate | PASS | 1.146 |
| GT-03 | Approved amendment | Phase 4 create_amendment | PASS | 0.013 |
| GT-04 | Revalidation and approval evidence | Phase 4 validate_amendment / ingest_amendments | PASS | 0.011 |
| GT-05 | Warehouse load and current-trade view | dbt models (SQLite mirror) | PASS | 0.007 |
| GT-06 | Simulated reporting outcome | Phase 4 reporting SQL (SQLite mirror) | PASS | 0.002 |
| GT-07 | Dashboard KPI reconciliation | Phase 4 KPI SQL vs Power BI | PASS | 0.002 |
| GT-08 | Rejection-risk prediction | Phase 6 FastAPI + Phase 5 model | PASS | 2.794 |
| GT-09 | Assistant explanation | Phase 6 AI Operations Assistant | PASS | 0.093 |

## GT-01 — Original capture

```json
{
  "fixture_files_verified": 4,
  "trades_captured": 50,
  "t1001_version": 1,
  "t1001_captured_notional": 100000000.0,
  "t1001_confirmed_notional": 10000000.0
}
```

## GT-02 — Validation, exception and publication

```json
{
  "batch_id": "BATCH-60FD5666D0A1FBAD",
  "validation_run_id": "VAL-115729AE7639",
  "total_trades": 50,
  "curated_records": 49,
  "quarantine_records": 1,
  "seeded_defects_detected": "10/10",
  "exception": {
    "trade_id": "T-1001",
    "trade_version": 1,
    "rule_id": "DEMO_NOTIONAL_MISMATCH",
    "status": "BLOCK",
    "detected_at_utc": "2026-11-10T15:25:22.716589+00:00",
    "source_checksum_sha256": "1d9e1bbf36b0ca6e7d8e2b8d96db05e37b77f34d524ec069932be3b93d5f3c30"
  },
  "processing_seconds": 1.14,
  "nfr001_limit_seconds": 60
}
```

## GT-03 — Approved amendment

```json
{
  "approval_reference": "NB-T1001-APP-001",
  "approved_by": "Project Owner - Trade Operations Reviewer",
  "approval_timestamp_utc": "2026-10-14T12:00:00Z",
  "new_version": 2,
  "corrected_notional": 10000000.0,
  "fields_compared_with_committed_v2": 19,
  "original_v1_notional_after_amendment": 100000000.0
}
```

## GT-04 — Revalidation and approval evidence

```json
{
  "v1_revalidation_rules": [
    "DEMO_NOTIONAL_MISMATCH"
  ],
  "v2_revalidation_rules": [],
  "v2_validation_status": "PASS",
  "v2_validation_run_id": "VAL-90BA7E7183AC",
  "approval_reference_linked": "NB-T1001-APP-001",
  "source_checksum_sha256": "1eea2e36711f5f47bd656a4e28b703af31f54758864d87c5f4a7a6e407ea0711",
  "verify_batch": [
    "APPROVAL_VERIFIED",
    "VALIDATION_VERIFIED",
    "SOURCE_CHECKSUM_VERIFIED"
  ]
}
```

## GT-05 — Warehouse load and current-trade view

```json
{
  "initial_batch_rows": 49,
  "current_trades_before_amendment": 49,
  "current_trades_after_amendment": 50,
  "t1001_current_version": 2,
  "t1001_current_notional": 10000000.0
}
```

## GT-06 — Simulated reporting outcome

```json
{
  "submissions_created": 50,
  "submissions_created_on_replay": 0,
  "t1001_submission_id": "SIM-T-1001-V2",
  "t1001_reporting_status": "ACCEPTED",
  "simulated_rejections": [
    "SIM-T-1010-V1",
    "SIM-T-1020-V1",
    "SIM-T-1030-V1",
    "SIM-T-1040-V1",
    "SIM-T-1050-V1"
  ],
  "note": "Simulated outcomes are positional (every 10th trade_id), not rule-based."
}
```

## GT-07 — Dashboard KPI reconciliation

```json
{
  "reconciled_kpis": 10,
  "values": {
    "total_trades": 50,
    "total_gbp_notional_m": 664.5,
    "current_validation_pass_rate_pct": 100.0,
    "initial_quarantine_rate_pct": 2.0,
    "simulated_reject_rate_pct": 10.0,
    "no_amendment_rate_pct": 98.0,
    "status_distribution": {
      "AMENDED": 1,
      "CAPTURED": 49
    },
    "counterparty_notional_m": {
      "CP-009": 169,
      "CP-004": 107,
      "CP-006": 85,
      "CP-003": 65,
      "CP-005": 55,
      "CP-002": 55,
      "CP-010": 54,
      "CP-007": 35,
      "CP-001": 30,
      "CP-008": 11
    },
    "t1001_original_notional_m": 100,
    "t1001_corrected_notional_m": 10
  },
  "dashboard_source": "Values as displayed on the Power BI 'Trade Operations & Validation Overview' page (NorthBridge.pbix), transcribed from image/README/1793484754266.png. Counterparty bars are displayed rounded to GBP millions."
}
```

## GT-08 — Rejection-risk prediction

```json
{
  "model_name": "Logistic Regression",
  "model_version": "1.0.0",
  "model_sha256": "29b46e6ab089522e2740a7475a435a83ca7e644e91d9123327e4d597668c8175",
  "threshold": 0.1,
  "scores": {
    "v1": {
      "notional": 100000000.0,
      "tenor_from_dates": 10.00137,
      "risk_score_tenor_from_dates": 0.18253,
      "risk_band_tenor_from_dates": "Flagged",
      "risk_score_tenor_10": 0.18252,
      "phase5_recorded_score": 0.18252
    },
    "v2": {
      "notional": 10000000.0,
      "tenor_from_dates": 10.00137,
      "risk_score_tenor_from_dates": 0.078752,
      "risk_band_tenor_from_dates": "Not Flagged",
      "risk_score_tenor_10": 0.078747,
      "phase5_recorded_score": 0.078747
    }
  }
}
```

## GT-09 — Assistant explanation

```json
{
  "llm": "TemplateLLM (offline stub)",
  "citations_used": [
    "CURATED T-1001 v2",
    "KB-001 v1.1 - Example: T-1001",
    "MODEL 1.0.0",
    "QUARANTINE BATCH-60FD5666D0A1FBAD"
  ],
  "unknown_citations": [],
  "warnings": [],
  "kb_sources": [
    "KB_001_Notional_Validation.md#Example: T-1001",
    "KB_003_Trade_Amendments.md#Example: T-1001 Amendment",
    "KB_004_Simulated_Reporting.md#Example: T-1001 Reporting Status",
    "KB_001_Notional_Validation.md#Validation Logic",
    "KB_002_Trade_Validation_Rules.md#Validation Rules"
  ],
  "model_risk_scored_version": 2,
  "model_risk_score": 0.078752,
  "files_checked_unchanged": 10
}
```
