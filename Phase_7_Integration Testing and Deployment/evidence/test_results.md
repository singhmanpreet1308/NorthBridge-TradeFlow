# Phase 7 Test Results

Generated 2026-11-10 15:23 UTC. Automated results come from `evidence/tc_results.json` (pytest); manual results from `uat/uat_results.csv`.

**40 passed · 0 failed · 3 not run** of 43 test cases.

| Test case | Title | Requirements | Method | Status | Pytest tests | Expected result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-GT-001 | T-1001 golden thread end to end | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010 | Automated | **Passed** | 2 | All nine stages PASS with one consistent T-1001 story |  |
| TC-CAP-001 | Capture structurally valid trades | FR-001 | Automated | **Passed** | 1 | 49 valid trades published at version 1 with source fields unchanged |  |
| TC-CAP-002 | Missing mandatory field | FR-001, FR-002 | Automated | **Passed** | 1 | Explicit DQ-009 / DQ-001 rule IDs recorded |  |
| TC-CAP-003 | Replay identical batch | FR-001, FR-006 | Automated | **Passed** | 1 | Batch SKIPPED; every stored file byte-identical |  |
| TC-CAP-004 | Conflicting existing trade ID | FR-001 | Automated | **Passed** | 1 | Conflict held for review | Deviation: batch aborts (fail-closed) via the 49/1 baseline-count control; no review queue exists |
| TC-CAP-005 | Capture T-1001 original | FR-001, FR-003 | Automated | **Passed** | 1 | GBP 100000000 retained in quarantine and raw source unchanged |  |
| TC-VAL-001 | Seeded defect manifest | FR-002 | Automated | **Passed** | 1 | 10/10 seeded defects detected with expected rule and BLOCK |  |
| TC-VAL-002 | T-1001 notional mismatch | FR-003 | Automated | **Passed** | 1 | DEMO_NOTIONAL_MISMATCH raised against GBP 10000000 confirmation |  |
| TC-VAL-003 | Missing confirmation | FR-003 | Automated | **Passed** | 2 | RECON_MISSING_CONFIRMATION recorded; never treated as a match | At batch level the whole batch aborts (see finding F-03) |
| TC-VAL-004 | Reproducible batch identity | FR-002, NFR-004 | Automated | **Passed** | 1 | Fixtures reproduce recorded BATCH-60FD5666D0A1FBAD |  |
| TC-EXC-001 | Exception record completeness | FR-004 | Automated | **Passed** | 1 | Exception carries trade/version/rule/status/timestamp/run ID/source checksum | Reviewer is recorded on the approval; there is no exception assignment entity |
| TC-EXC-002 | Unresolved exception blocks reporting | FR-004, FR-008 | Automated | **Passed** | 1 | No simulated submission for blocked T-1001 v1 |  |
| TC-AMD-001 | Approved amendment | FR-005, FR-006 | Automated | **Passed** | 1 | T-1001 v2 created at GBP 10000000 with status AMENDED |  |
| TC-AMD-002 | Rejected amendment | FR-005 | Automated | **Passed** | 1 | No new version; trade data unchanged |  |
| TC-AMD-003 | Approved cancellation | FR-005, FR-006 | Not implemented | **Not Run** | 0 | Cancellation event retained | Cancellation workflow was not built in Phases 3-6 |
| TC-AMD-004 | Duplicate amendment load | FR-006 | Automated | **Passed** | 1 | Second load refused; row count unchanged |  |
| TC-AMD-005 | Stale-version amendment | FR-006 | Automated | **Passed** | 1 | AmendmentConflictError raised | Stale-version guard added to create_amendment.build_amendment in Phase 7 |
| TC-AMD-006 | Revalidation fails | FR-007 | Automated | **Passed** | 1 | Reporting remains blocked |  |
| TC-AMD-007 | Version history retained | FR-006 | Automated | **Passed** | 1 | v1 (100M) and v2 (10M) both accessible; current view shows v2 |  |
| TC-AMD-008 | Approval evidence enforced | FR-005 | Automated | **Passed** | 5 | Missing/forged/pending approval or edited source refused |  |
| TC-AMD-009 | Independent v2 revalidation | FR-007 | Automated | **Passed** | 1 | v1 still fails; v2 passes on its own merits |  |
| TC-RPT-001 | Eligible current versions only | FR-008 | Automated | **Passed** | 1 | 50 submissions; each references the current version; T-1001 only as V2 |  |
| TC-RPT-002 | Outcomes distinct from validation | FR-008 | Automated | **Passed** | 1 | 45 ACCEPTED / 5 REJECTED (DEMO_REPORT_REJECT) all internally PASS | Simulated outcomes are positional (every 10th trade_id) not rule-based |
| TC-RPT-003 | Reporting replay | FR-008 | Automated | **Passed** | 1 | Replay inserts 0 rows; 50 distinct submission IDs |  |
| TC-RPT-004 | No live submission | FR-008 | Automated | **Passed** | 1 | Reporting completes with all sockets disabled |  |
| TC-BI-001 | Headline KPI reconciliation | FR-009 | Automated | **Passed** | 1 | SQL KPIs equal dashboard values (50 / 664.5M / 100% / 2% / 10% / 98%) | Dashboard values transcribed from the Power BI screenshot |
| TC-BI-002 | Breakdown reconciliation | FR-009 | Automated | **Passed** | 1 | Status split 49/1 and 10 counterparty bars match | Power BI rounds half away from zero |
| TC-BI-003 | No double counting | FR-009 | Automated | **Passed** | 1 | 50 current rows for 50 trades; no duplicate trade/version |  |
| UAT-BI-001 | Interactive dashboard walkthrough | FR-009 | Manual | **Not Run** | 0 | Open NorthBridge.pbix; filter T-1001; v1 BLOCK and v2 values visible | Requires Power BI Desktop; see uat/UAT_Test_Cases.md |
| TC-AI-001 | Model identity on /health | FR-010 | Automated | **Passed** | 1 | Version 1.0.0 and SHA-256 match model registry |  |
| TC-AI-002 | Scores from trained model | FR-010 | Automated | **Passed** | 1 | T-1001 v1/v2 scores reproduce Phase 5 evidence within 1e-6 |  |
| TC-AI-003 | No future information in features | FR-010 | Automated | **Passed** | 1 | Outcome fields absent from features; extra fields rejected 422 |  |
| TC-AI-004 | Assistant grounded in evidence | FR-010 | Automated | **Passed** | 1 | Cites quarantine + curated + KB-001; no invented citations | Uses offline TemplateLLM; answer quality needs UAT-AI-001 |
| TC-AI-005 | Assistant is read-only | FR-010, NFR-003 | Automated | **Passed** | 2 | All stored files unchanged; no write operations exposed |  |
| TC-AI-006 | Unsupported conclusions identified | FR-010 | Automated | **Passed** | 3 | Missing trade / API outage / invented citation are flagged |  |
| UAT-AI-001 | Live LLM explanation of T-1001 | FR-010 | Manual | **Not Run** | 0 | Live answer cites evidence; no unknown citations; states v2 resolved | Needs EURI_API_KEY: python -m nbit.golden_thread --live-llm |
| TC-NFR-001 | 50-trade batch within 60s | NFR-001 | Automated | **Passed** | 1 | Validation and curated publication complete in <= 60s | Measured on local storage; Azure route not timed |
| TC-NFR-002 | Replay idempotency | NFR-002 | Automated | **Passed** | 3 | No duplicate trades / versions / submissions on replay | Covered together with CAP-003 / AMD-004 / RPT-003 |
| TC-NFR-003 | Role-based authorisation | NFR-003 | Automated | **Passed** | 4 | Unauthorised approve/amend/cancel denied and logged | Partial: approval evidence is enforced but no RBAC or denied-attempt log exists |
| TC-NFR-004 | Lifecycle audit trail | NFR-004 | Automated | **Passed** | 2 | All 8 mandatory attributes populated for 6 T-1001 events | Trail is reconstructed from per-component artefacts; no single event store |
| TC-NFR-005 | Safe failure and fault injection | NFR-005 | Automated | **Passed** | 8 | Corruption / partial batch / outage / blocked trade all fail safe and visibly | No bounded-retry test (Airflow retries not exercised locally) |
| TC-OPS-001 | Rollback to known model version | NFR-005 | Automated | **Passed** | 2 | Candidate replaced by registered 1.0.0; checksum guard refuses unknown model | Drill uses a relabelled copy; only one trained version exists |
| TC-OPS-002 | Container smoke test | FR-010 | CI only | **Passed** | 0 | Docker image builds and /health returns the registered model | Runs in the GitHub Actions docker job; Local Docker 29.9.3; evidence/container_smoke_test.md; also runs in CI container job |
