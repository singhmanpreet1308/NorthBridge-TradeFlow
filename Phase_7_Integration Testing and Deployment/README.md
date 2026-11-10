# Phase 7 — Integration Testing, Deployment & Portfolio

Proves that the components built in Phases 1–6 form **one reproducible system**, closes the requirements traceability chain, and packages an honest demonstration.

## Quick start

```bash
cd "Phase_7_Integration Testing and Deployment"
pip install -r requirements-ci.txt          # or use the NorthBridge_TradeFlow conda env

python -m nbit.run_all                      # tests + golden thread + RTM  (~15 s)
python -m nbit.golden_thread                # golden thread only
python -m pytest -q                         # test suite only
python -m nbit.run_all --update-tracker     # also write results into Delivery_Tracker.xlsx
```

Nothing external is needed: no Azure, Snowflake, LLM key or running API. The harness works in a temporary sandbox and never writes to `azure_backup/`.

## What is in this folder

| Path | Purpose |
| --- | --- |
| `nbit/golden_thread.py` | Runs T-1001 through all nine stages using the real phase code |
| `nbit/components.py` | Loads Phase 3/4/6 modules and points Phase 3 storage at a sandbox |
| `nbit/warehouse.py` | SQLite port of the dbt views, simulated-reporting INSERT and KPI SQL |
| `nbit/audit_trail.py` | Reconstructs the T-1001 lifecycle audit trail (NFR-004) |
| `nbit/traceability.py` | Builds the RTM from saved results; optionally updates the tracker |
| `tests/` | 49 integration, UAT, NFR and operations tests, each tagged with test-case IDs |
| `fixtures/` | Byte-exact raw inputs, their checksums, and the dashboard's displayed values |
| `traceability/` | Requirement register (with known gaps) and test-case catalogue |
| `uat/` | Manual UAT scripts and results |
| `ops/` | Runbook, docker-compose, model registry |
| `docs/` | Architecture, findings, portfolio map, evidence index |
| `evidence/` | Generated results — regenerate, don't edit |

## The golden thread

| Stage | What runs | T-1001 result |
| --- | --- | --- |
| GT-01 Capture | Fixture checksums verified | v1, GBP 100,000,000 retained |
| GT-02 Validation | Phase 3 `validate.main()` unchanged | `DEMO_NOTIONAL_MISMATCH` → BLOCK, quarantined; 49/1; batch `BATCH-60FD5666D0A1FBAD` reproduced |
| GT-03 Amendment | Phase 4 `build_amendment` + approval | v2 at GBP 10,000,000; identical to committed v2; v1 untouched |
| GT-04 Revalidation | Phase 4 `revalidate`, `verify_batch` | v2 PASS; approval `NB-T1001-APP-001` and checksum verified |
| GT-05 Warehouse | dbt view logic | Current trades 49 → 50; T-1001 current = v2 |
| GT-06 Reporting | Simulated reporting SQL | `SIM-T-1001-V2` ACCEPTED; replay adds 0 |
| GT-07 Dashboard | KPI SQL vs Power BI values | 50 · £664.5M · 100% · 2% · 10% · 98% — all match |
| GT-08 Prediction | FastAPI + model 1.0.0 | v1 0.1825 Flagged · v2 0.0788 Not Flagged; matches Phase 5 |
| GT-09 Assistant | Ops assistant + retriever | Cites quarantine, curated v2, KB-001, model; no stored file changed |

## Results

See [`evidence/test_results.md`](evidence/test_results.md) and [`evidence/RTM.md`](evidence/RTM.md).

- **43 test cases: 40 passed, 0 failed, 3 not run.** The 49 pytest tests all pass, plus the container smoke test.
- **All 15 Must requirements** (10 FR + 5 NFR) have linked tests.
- **4 are Verified** outright; **9 pass with stated gaps**; **2 are In Progress** because a core criterion was never built (role-based authorisation for FR-005 / NFR-003).
- **Not run:** TC-AMD-003 (trade cancellation was never built), and two manual UAT cases, the Power BI walkthrough and the live-LLM answer review (scripts in `uat/`).

Gaps and open issues are listed in [`docs/INTEGRATION_FINDINGS.md`](docs/INTEGRATION_FINDINGS.md).

## Changes made to earlier phases

| File | Change | Why |
| --- | --- | --- |
| `Phase_4…/amendments/create_amendment.py` | Fixed Phase 3 path; logic in `build_amendment()`; stale-version guard | Script referenced a renamed folder (F-02); TC-AMD-005 |
| `Phase_4…/amendments/validate_amendment.py` | Fixed path; logic in `revalidate()` / `build_validated_batch()` | F-02; importable for integration |
| `Phase_4…/amendments/ingest_amendments.py` | Snowflake imports moved inside `connect_snowflake()` | Run `verify_batch` offline (F-09) |
| `Phase_6…/app/main.py` | `NB_MODEL_DIR`, `NB_EXPECTED_MODEL_SHA256`, `model_sha256` in `/health` | Rollback and model-identity monitoring |
| `.gitattributes` (new) | Byte-exact evidence files | Stop line-ending conversion changing checksums |
| `.github/workflows/ci.yml` (new) | CI for core checks | Phase 7 scope |

Script behaviour when run directly is unchanged; existing Phase 3 (20) and Phase 6 (30) tests still pass.

## Operations

[`ops/RUNBOOK.md`](ops/RUNBOOK.md) covers startup, configuration, teardown, monitoring signals, rollback to a known model version, and failure/replay behaviour.
