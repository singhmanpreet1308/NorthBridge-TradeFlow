# UAT Test Cases — NorthBridge TradeFlow

Most acceptance checks are automated (`tests/`, see `evidence/test_results.md`). Two need a person, because they need judgement or a desktop tool:

| ID | Requirement | Why it is manual |
| --- | --- | --- |
| UAT-BI-001 | FR-009 | Power BI Desktop cannot run in CI. The KPI *values* are reconciled automatically (TC-BI-001/002). This case checks that the dashboard itself behaves correctly. |
| UAT-AI-001 | FR-010 | CI uses an offline template LLM to test plumbing, citations and read-only behaviour. Whether the live LLM's *explanation* is correct and useful needs a reviewer. |

After running a case, record the outcome in [`uat_results.csv`](uat_results.csv) (`Passed`, `Failed` or `Blocked`) and rebuild the RTM:

```bash
python -m nbit.traceability --update-tracker
```

A blank status is reported as **Not Run**. Do not mark a case Passed without saving the evidence named below.

---

## UAT-BI-001 — Interactive dashboard walkthrough

**Role:** Analytics User · **Pre-condition:** Power BI Desktop; Snowflake access, or the last saved data in the .pbix.

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Open `Phase_4_Analytics_ &_Regulatory Intelligence/NorthBridge.pbix` | Report opens on *Trade Operations & Validation Overview* |
| 2 | Read the KPI cards | Total Trades **50** · Total GBP Notional **£664.5M** · Current Validation Pass Rate **100%** · Initial Quarantine Rate **2%** · Simulated Reject **10%** · No-Amendment Rate **98%** |
| 3 | Compare with `evidence/golden_thread/golden_thread_report.md` → GT-07 | Every card equals the SQL value |
| 4 | Set the **TRADE ID** slicer to `T-1001` | Original notional **£100M**, corrected **£10M**; table shows v1 with **BLOCK** |
| 5 | Check the T-1001 table's `Validation_run_id` | Known issue F-06: the dashboard shows `VAL-61AFEC9B6CC3` (policy 1.0 batch) while KPI SQL uses `BATCH-60FD5666D0A1FBAD` (policy 1.1). Note which one is shown. |
| 6 | Clear the slicer | Status chart: CAPTURED 49, AMENDED 1 · CP-009 is the largest counterparty bar (169M) |

**Evidence:** screenshot after step 4 saved as `evidence/uat/UAT-BI-001_t1001.png`.

---

## UAT-AI-001 — Live LLM explanation of T-1001

**Role:** Trade Operations Analyst · **Pre-condition:** `Phase_6_ML Engineering/.env` contains `EURI_API_KEY`.

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | From the Phase 7 folder run `python -m nbit.golden_thread --live-llm --out evidence/uat/live_llm` | All nine stages PASS (GT-09 uses the real LLM) |
| 2 | Open `evidence/uat/live_llm/assistant_answer.md` | Answer has the five required sections |
| 3 | Check the *Answer* section | States v1 was blocked by `DEMO_NOTIONAL_MISMATCH` (100M vs 10M confirmation) and that v2 passed revalidation, so the exception is resolved |
| 4 | Check the *Model risk* section | Reports score ≈ 0.0788, *Not Flagged*, threshold 0.10, model 1.0.0 — and does **not** use the score to explain the block |
| 5 | Check *Recommended next steps* | Recommends only human actions; claims nothing was approved, amended or submitted by the assistant |
| 6 | Check the *Citation check* block | `unknown_citations` is empty; at least one `KB-` citation |

**Evidence:** the `evidence/uat/live_llm/` folder.

**Fail if:** any factual sentence lacks a citation, the score is presented as a validation result, or the answer recommends re-doing steps the evidence shows are complete.
