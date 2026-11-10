# Portfolio Map

A guide to what was built, where it is, and what proves it works. For a reviewer with 10 minutes: read §1, run §3, skim `evidence/RTM.md`.

## 1. What this project is — and is not

**Is:** an end-to-end, reproducible demonstration of an OTC trade-lifecycle control system for GBP interest rate swaps. One trade (T-1001) is followed from a wrong capture (GBP 100M vs a 10M confirmation) through detection, human-approved correction, revalidation, simulated reporting, analytics, a risk score and an AI explanation. Every step runs real code and is checked by automated tests.

**Is not:**
- Real trading data. All 50 trades and confirmations are synthetic; only the Phase 5 drift check used real (public CME) data.
- Regulatory reporting. Reporting outcomes are simulated and **positional** (every 10th trade is "rejected"); nothing is sent to a trade repository.
- A validated risk model. The model learns *simulated* rejection labels; PR-AUC 0.138 on synthetic data. It is a working ML pipeline, not evidence of predictive power.
- Production access control. Approval evidence is enforced, but there is no role-based authorisation.

## 2. Phase by phase

| Phase | Question it answers | What was built | Key artefacts | Proof |
| --- | --- | --- | --- | --- |
| 1 · Foundation | What is the business problem? | Domain analysis, AS-IS process, synthetic trades with seeded defects | `docs/Foundation.md`, `data/Phase_1`, `diagrams/Phase_1` | Seeded-defect manifest used by every later test |
| 2 · Design | What exactly must it do? | 10 FRs, 5 NFRs, use cases, API/security design, roadmap, RAID | `docs/Design.md`, `data/Phase_2/Delivery_Tracker.xlsx`, `diagrams/Phase_2` | RTM now filled from test results |
| 3 · Data engineering | Can trades be validated and published safely? | Validation rules, confirmation reconciliation, quarantine, checksummed idempotent batches, Snowflake + dbt, Airflow | `Phase_3…/pipeline`, `northbridge_dbt`, `airflow` | Batch ID reproduced; replay, corruption and partial-batch tests |
| 4 · Analytics & controls | Can errors be corrected under control and monitored? | Approval → amendment → revalidation → controlled load; simulated reporting; KPI SQL; Power BI | `Phase_4…/amendments`, `KPI_SQL.txt`, `NorthBridge.pbix` | Dashboard KPIs reconciled to SQL (TC-BI-001/002) |
| 5 · Data science | Can rejection risk be estimated before submission? | 5 models compared, leakage checks, SHAP, model card, real CME drift check | `Phase_5…/notebook`, `Model_Card.md` | T-1001 scores reproduced by the API to 1e-6 |
| 6 · ML engineering & AI | Can the model and evidence be served to operations staff? | FastAPI + Docker, BM25 RAG over versioned notes, citation-checked read-only assistant | `Phase_6…/app`, `assistant`, `knowledge` | Container smoke test; grounding and read-only tests |
| 7 · Integration | Do the parts form one reproducible system? | Golden thread, 49 integration/UAT tests, generated RTM, CI, runbook, rollback | `Phase_7…` | `evidence/`, GitHub Actions |

## 3. Five-minute demonstration

Run from `Phase_7_Integration Testing and Deployment` in the project environment.

| # | Do | Say | Point at |
| --- | --- | --- | --- |
| 1 | `python -m nbit.golden_thread` | "One command replays T-1001 across all six build phases in about 4 seconds, from committed inputs." | Nine PASS lines |
| 2 | Open `evidence/golden_thread/golden_thread_report.md` → GT-02 | "The batch ID is a hash of the inputs, so a clean checkout reproduces the exact batch Phase 3 published in October: `BATCH-60FD5666D0A1FBAD`." | `batch_id`, `exception` |
| 3 | Same file → GT-03/04 | "The correction needs a recorded approval. The rebuilt v2 matches the committed one field for field, and v1 is never modified." | `approval_reference`, `v2_revalidation_rules: []` |
| 4 | GT-06/07 | "Only the corrected version is submitted. Re-running creates zero duplicates. Every dashboard number is recomputed from SQL and matches the Power BI page." | `SIM-T-1001-V2`, `submissions_created_on_replay: 0` |
| 5 | `evidence/golden_thread/assistant_answer.md` | "The assistant only sees retrieved evidence, keeps the model score separate from the validation result, and every citation is checked. It cannot change data: every stored file is hashed before and after." | Evidence pack, citation check |
| 6 | `evidence/RTM.md` | "Only 4 of 15 requirements are fully Verified. The rest pass their tests but have stated gaps — no RBAC, simulated reporting is positional. I'd rather show that than overclaim." | Status column |

**Be ready for:** *"Is the model any good?"* — No claim of real predictive power: synthetic labels, PR-AUC 0.138, and on real CME data all four alerts were outside the training ranges (drift). *"Why SQLite?"* — CI must not need cloud credentials; the same dbt and KPI SQL are ported, and the Snowflake run is evidenced separately in Phase 3/4.

## 4. Skills evidenced

| Area | Evidence |
| --- | --- |
| Business analysis | Business needs → FRs → user stories → test cases → results (`evidence/RTM.md`) |
| Data engineering | Idempotent, checksummed batches; quarantine; dbt version views; replay and fault-injection tests |
| Data governance | Lineage (source checksums on every record), approval evidence, no-overwrite storage |
| Analytics | KPI SQL reconciled to the dashboard, including the rounding convention |
| Data science | Model comparison, leakage control, SHAP, external drift check, honest model card |
| ML engineering | Containerised API, model fingerprinting, checksum-pinned rollback |
| AI engineering | Retrieval-grounded assistant, citation verification, read-only enforcement tested |
| Quality & delivery | 49-test integration suite, generated traceability, CI, runbook, findings log |
