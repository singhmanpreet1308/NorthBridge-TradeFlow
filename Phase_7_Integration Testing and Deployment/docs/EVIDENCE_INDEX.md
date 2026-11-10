# Evidence Index

Every claim in the README should point to one of these. Paths are relative to the repository root; `P7` = `Phase_7_Integration Testing and Deployment`.

**Regenerate** all Phase 7 evidence: `cd P7 && python -m nbit.run_all --update-tracker`.

## Phase 7 — integration and UAT

| ID | Evidence | Path | Proves | Requirements |
| --- | --- | --- | --- | --- |
| EV-701 | Golden thread run report | `P7/evidence/golden_thread/golden_thread_report.md` | T-1001 passes all 9 stages, with ids, counts, timings | FR-001…FR-010 |
| EV-702 | Golden thread machine record | `P7/evidence/golden_thread/golden_thread_run.json` | Same, full detail incl. environment | FR-001…FR-010 |
| EV-703 | Phase 3 batch console log (sandbox) | `P7/evidence/golden_thread/phase3_batch_log.txt` | Real `validate.main()` output: manifest 10/10, 49/1, integrity checks | FR-002, FR-003, NFR-005 |
| EV-704 | Assistant answer + evidence pack | `P7/evidence/golden_thread/assistant_answer.md` | Exactly what the LLM was given; citation check | FR-010 |
| EV-705 | Test-case results | `P7/evidence/test_results.md` | Status of every TC with pytest test count | All |
| EV-706 | Per-test raw results | `P7/evidence/tc_results.json`, `P7/evidence/pytest_junit.xml` | Machine-readable outcomes per test | All |
| EV-707 | Requirements traceability matrix | `P7/evidence/RTM.md`, `RTM.csv` | Every Must requirement → tests → result → gaps | All |
| EV-708 | Delivery tracker (updated) | `data/Phase_2/Delivery_Tracker.xlsx` (RTM, User_Stories, Release_Tracker, Phase7_Test_Results) | Same RTM in the Phase 2 tracking artefact | All |
| EV-709 | Container smoke test | `P7/evidence/container_smoke_test.md` | Image runs, serves registered model, refuses unknown model | FR-010, TC-OPS-002 |
| EV-710 | CI run | GitHub Actions → *NorthBridge TradeFlow CI* → artifact `phase7-evidence` | Checks re-run on every push from a clean checkout | All |
| EV-711 | Integration findings | `P7/docs/INTEGRATION_FINDINGS.md` | What broke, what was fixed, what is open | — |
| EV-712 | Fixture provenance | `P7/fixtures/fixture_manifest.json` | Committed inputs are byte-identical to the Phase 3 inputs | NFR-004 |
| EV-713 | Dashboard reference values | `P7/fixtures/expected_dashboard_kpis.json` + `image/README/1793484754266.png` | Values the SQL is reconciled against | FR-009 |
| EV-714 | Model registry | `P7/ops/model_registry.json` | Known-good model version + checksum for rollback | FR-010 |
| EV-715 | Manual UAT record | `P7/uat/uat_results.csv`, `P7/uat/UAT_Test_Cases.md` | Manual cases and their status (two pending) | FR-009, FR-010 |

## Earlier phases (referenced, not regenerated)

| ID | Evidence | Path | Proves |
| --- | --- | --- | --- |
| EV-301 | Phase 3 batch audit (policy 1.1) | `Phase_3…/azure_backup/curated/audit/BATCH-60FD5666D0A1FBAD/` *(git-ignored, local only)* | Original publication the golden thread reproduces |
| EV-302 | Phase 3 unit tests | `Phase_3…/pipeline/test_validate.py` (20 tests) | Each DQ rule; checksum verification |
| EV-401 | T-1001 approval | `Phase_4…/amendments/T1001_Approval.json` | Human approval `NB-T1001-APP-001` |
| EV-402 | T-1001 v2 validated batch + audit | `Phase_4…/amendments/validated_output/` | v2 PASS, run `VAL-90BA7E7183AC`, source checksum `1eea2e36…` |
| EV-403 | Power BI dashboard | `Phase_4…/NorthBridge.pbix`, `image/README/1793484754266.png` | Dashboard KPIs |
| EV-501 | Model card | `Phase_5…/notebook/Model_Card.md` | Metrics, threshold, limitations |
| EV-502 | T-1001 Phase 5 scores | `Phase_5…/notebook/evidence/T1001_model_predictions.csv` | v1 0.1825 / v2 0.0787 (reproduced by GT-08) |
| EV-503 | MLflow run | `Phase_6…/mlruns/394662252900529438/d9664af6…` | Logged params/metrics for model 1.0.0 |
| EV-601 | Phase 6 tests | `Phase_6…/tests/` (30 tests) | API contract, retriever, assistant grounding |
| EV-602 | Assistant UI screenshot (live LLM) | `image/README/1794268713285.png` | Earlier live-LLM run (Phase 6, not re-executed in Phase 7) |
