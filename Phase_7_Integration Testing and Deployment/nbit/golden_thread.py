"""T-1001 golden thread: one end-to-end run across every phase.

    capture -> validation/exception -> approved amendment -> revalidation
    -> warehouse load -> simulated reporting -> dashboard KPIs
    -> prediction -> assistant explanation

Usage (from the Phase 7 folder):
    python -m nbit.golden_thread                  # offline, writes evidence/
    python -m nbit.golden_thread --live-llm       # also calls the real LLM
    python -m nbit.golden_thread --workdir PATH   # keep the sandbox
"""

import argparse
import json
import platform
import re
import sys
import tempfile
import time
import traceback
from contextlib import redirect_stdout
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from io import StringIO
from pathlib import Path

import pandas as pd

from nbit import components, paths
from nbit.warehouse import Warehouse

TRADE_ID = "T-1001"
NFR001_LIMIT_SECONDS = 60
AMENDMENT_VOLATILE_FIELDS = {"record_timestamp"}


class StageFailure(AssertionError):
    pass


def check(condition, message):
    if not condition:
        raise StageFailure(message)


def round_half_up(value):
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# Offline LLM stand-in. It only rearranges evidence tags so the pipeline,
# citation checker and read-only behaviour can be tested without a network.
# It says nothing about answer quality; that needs the live LLM (UAT-AI-001).
class TemplateLLM:
    name = "TemplateLLM (offline stub)"

    def __call__(self, messages):
        evidence = messages[1]["content"]
        tags = re.findall(r"^\[([^\]]+)\]", evidence, flags=re.MULTILINE)
        quarantine = next((t for t in tags if t.startswith("QUARANTINE")), None)
        curated = next((t for t in tags if t.startswith("CURATED")), None)
        model = next((t for t in tags if t.startswith("MODEL")), None)
        kb = next((t for t in tags if t.startswith("KB-")), None)

        lines = ["**Answer** - Template answer assembled from evidence tags only."]
        if quarantine:
            lines.append(f"Version 1 was blocked [{quarantine}].")
        if curated:
            lines.append(f"The current version passed revalidation [{curated}].")
        if kb:
            lines.append(f"The applicable procedure is documented [{kb}].")
        lines.append("**Model risk (separate from validation)** - "
                     + (f"see [{model}]." if model else "[NOT AVAILABLE]."))
        lines.append("**Evidence gaps** - None.")
        return {"status": "success", "content": "\n".join(lines)}


class GoldenThread:

    def __init__(self, workdir, live_llm=False):
        self.workdir = Path(workdir)
        self.sandbox = self.workdir / "storage"
        self.live_llm = live_llm
        self.stages = []
        self.ctx = {}

    # Runner
    def run(self):
        started = time.perf_counter()
        steps = [
            ("GT-01", "Original capture", "Phase 1 fixtures", self.stage_capture),
            ("GT-02", "Validation, exception and publication", "Phase 3 pipeline.validate", self.stage_validation),
            ("GT-03", "Approved amendment", "Phase 4 create_amendment", self.stage_amendment),
            ("GT-04", "Revalidation and approval evidence", "Phase 4 validate_amendment / ingest_amendments", self.stage_revalidation),
            ("GT-05", "Warehouse load and current-trade view", "dbt models (SQLite mirror)", self.stage_warehouse),
            ("GT-06", "Simulated reporting outcome", "Phase 4 reporting SQL (SQLite mirror)", self.stage_reporting),
            ("GT-07", "Dashboard KPI reconciliation", "Phase 4 KPI SQL vs Power BI", self.stage_dashboard),
            ("GT-08", "Rejection-risk prediction", "Phase 6 FastAPI + Phase 5 model", self.stage_prediction),
            ("GT-09", "Assistant explanation", "Phase 6 AI Operations Assistant", self.stage_assistant),
        ]

        blocked_by = None
        for stage_id, name, component, fn in steps:
            record = {"id": stage_id, "name": name, "component": component}
            if blocked_by:
                record.update(status="BLOCKED", detail=f"Not run: {blocked_by} failed.")
                self.stages.append(record)
                continue

            t0 = time.perf_counter()
            try:
                facts = fn()
                record.update(status="PASS", facts=facts)
            except Exception as exc:
                record.update(
                    status="FAIL",
                    detail=f"{type(exc).__name__}: {exc}",
                    traceback=traceback.format_exc(limit=4),
                )
                blocked_by = stage_id
            record["duration_seconds"] = round(time.perf_counter() - t0, 3)
            self.stages.append(record)

        return {
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "trade_id": TRADE_ID,
            "status": "PASS" if all(s["status"] == "PASS" for s in self.stages) else "FAIL",
            "total_seconds": round(time.perf_counter() - started, 3),
            "llm_mode": "live" if self.live_llm else TemplateLLM.name,
            "environment": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "pandas": pd.__version__,
            },
            "stages": self.stages,
        }

    # GT-01
    def stage_capture(self):
        manifest = json.loads(paths.FIXTURE_MANIFEST.read_text(encoding="utf-8"))
        for rel, info in manifest["files"].items():
            actual = components.sha256_file(paths.RAW_FIXTURES / rel)
            check(actual == info["sha256"], f"Fixture checksum changed: {rel}")

        components.seed_sandbox(self.sandbox)
        trades = pd.read_csv(self.sandbox / "raw" / "trades" / "sample_trades.csv")
        confirmations = pd.read_csv(
            self.sandbox / "raw" / "confirmations" / "independent_confirmations.csv"
        )
        original = trades[trades["trade_id"] == TRADE_ID]

        check(len(original) == 1, "T-1001 must appear exactly once at capture.")
        check(int(original.iloc[0]["trade_version"]) == 1, "T-1001 must start at v1.")
        check(float(original.iloc[0]["notional_amount"]) == 100_000_000,
              "Captured notional must be retained as GBP 100,000,000.")

        confirmed = confirmations[confirmations["trade_id"] == TRADE_ID]
        self.ctx.update(trades=trades, confirmations=confirmations)

        return {
            "fixture_files_verified": len(manifest["files"]),
            "trades_captured": len(trades),
            "t1001_version": 1,
            "t1001_captured_notional": float(original.iloc[0]["notional_amount"]),
            "t1001_confirmed_notional": float(confirmed.iloc[0]["notional_amount"]),
        }

    # GT-02
    def stage_validation(self):
        t0 = time.perf_counter()
        log = components.run_phase3_batch(self.sandbox)
        elapsed = time.perf_counter() - t0

        batch = components.find_batch(self.sandbox)
        summary = json.loads(batch["summary"].read_text(encoding="utf-8"))
        quarantine = pd.read_csv(batch["quarantine"])
        curated = pd.read_csv(batch["curated"])
        manifest = json.loads(paths.FIXTURE_MANIFEST.read_text(encoding="utf-8"))

        check(batch["batch_id"] == manifest["recorded_batch_id"],
              f"Batch ID {batch['batch_id']} does not reproduce the recorded "
              f"{manifest['recorded_batch_id']}.")
        check(summary["curated_records"] + summary["quarantine_records"]
              == summary["total_trades"] == 50, "Batch counts do not reconcile.")
        check(summary["manifest_tests_passed"] == summary["manifest_tests_total"] == 10,
              "Seeded-defect manifest did not pass 10/10.")
        check(list(quarantine["trade_id"]) == [TRADE_ID], "Only T-1001 should be quarantined.")

        exception = quarantine.iloc[0]
        rules = json.loads(exception["detected_rules"])
        check(rules == ["DEMO_NOTIONAL_MISMATCH"], f"Unexpected rules {rules}")
        check(exception["validation_status"] == "BLOCK", "T-1001 v1 must be BLOCK.")
        check(float(exception["notional_amount"]) == 100_000_000,
              "Quarantine must keep the original notional.")
        check(TRADE_ID not in set(curated["trade_id"]), "Blocked trade leaked into curated.")
        check(elapsed <= NFR001_LIMIT_SECONDS, f"NFR-001 breached: {elapsed:.1f}s")

        (self.workdir / "phase3_batch_log.txt").write_text(log, encoding="utf-8")
        self.ctx.update(batch=batch, summary=summary)

        return {
            "batch_id": batch["batch_id"],
            "validation_run_id": summary["validation_run_id"],
            "total_trades": summary["total_trades"],
            "curated_records": summary["curated_records"],
            "quarantine_records": summary["quarantine_records"],
            "seeded_defects_detected": f"{summary['manifest_tests_passed']}/{summary['manifest_tests_total']}",
            "exception": {
                "trade_id": exception["trade_id"],
                "trade_version": int(exception["trade_version"]),
                "rule_id": rules[0],
                "status": exception["validation_status"],
                "detected_at_utc": exception["validated_at_utc"],
                "source_checksum_sha256": exception["source_checksum_sha256"],
            },
            "processing_seconds": round(elapsed, 3),
            "nfr001_limit_seconds": NFR001_LIMIT_SECONDS,
        }

    # GT-03
    def stage_amendment(self):
        create = components.phase4_create_amendment()
        approval = components.load_approval()

        amended = create.build_amendment(self.ctx["trades"], approval)
        committed = pd.read_csv(paths.AMENDMENT_SOURCE)

        compared = [c for c in committed.columns if c not in AMENDMENT_VOLATILE_FIELDS]
        mismatched = [
            c for c in compared
            if str(amended.iloc[0][c]) != str(committed.iloc[0][c])
        ]
        check(not mismatched, f"Rebuilt v2 differs from committed v2 on {mismatched}")

        # The original record is untouched by the amendment.
        original = self.ctx["trades"][self.ctx["trades"]["trade_id"] == TRADE_ID]
        check(float(original.iloc[0]["notional_amount"]) == 100_000_000,
              "Amendment modified the original version.")

        self.ctx.update(approval=approval, amended=committed)
        return {
            "approval_reference": approval["approval_reference"],
            "approved_by": approval["approved_by"],
            "approval_timestamp_utc": approval["approval_timestamp_utc"],
            "new_version": int(amended.iloc[0]["trade_version"]),
            "corrected_notional": float(amended.iloc[0]["notional_amount"]),
            "fields_compared_with_committed_v2": len(compared),
            "original_v1_notional_after_amendment": 100_000_000.0,
        }

    # GT-04
    def stage_revalidation(self):
        revalidate = components.phase4_validate_amendment().revalidate
        ingest = components.phase4_ingest_amendments()
        confirmations = self.ctx["confirmations"]

        v1 = self.ctx["trades"][self.ctx["trades"]["trade_id"] == TRADE_ID].iloc[0]
        v2 = self.ctx["amended"].iloc[0]
        v1_rules = revalidate(v1, confirmations)
        v2_rules = revalidate(v2, confirmations)

        check(v1_rules == ["DEMO_NOTIONAL_MISMATCH"], f"v1 rules {v1_rules}")
        check(v2_rules == [], f"v2 should pass revalidation, got {v2_rules}")

        out = StringIO()
        with redirect_stdout(out):
            columns, row = ingest.verify_batch(
                paths.AMENDMENT_VALIDATED, paths.AMENDMENT_AUDIT,
                paths.APPROVAL_FILE, paths.AMENDMENT_SOURCE,
            )
        printed = out.getvalue()
        for marker in ("APPROVAL_VERIFIED", "VALIDATION_VERIFIED", "SOURCE_CHECKSUM_VERIFIED"):
            check(marker in printed, f"verify_batch did not report {marker}")

        audit = json.loads(paths.AMENDMENT_AUDIT.read_text(encoding="utf-8"))
        self.ctx.update(amendment_columns=columns, amendment_row=row)

        return {
            "v1_revalidation_rules": v1_rules,
            "v2_revalidation_rules": v2_rules,
            "v2_validation_status": "PASS",
            "v2_validation_run_id": audit["validation_run_id"],
            "approval_reference_linked": audit["approval_reference"],
            "source_checksum_sha256": audit["source_checksum_sha256"],
            "verify_batch": [m for m in printed.splitlines() if m.endswith("VERIFIED")],
        }

    # GT-05
    def stage_warehouse(self):
        wh = Warehouse()
        loaded = wh.load_curated_batch(self.ctx["batch"]["curated"])
        before = wh.scalar("SELECT COUNT(*) FROM int_current_trades")
        wh.load_amendment(self.ctx["amendment_columns"], self.ctx["amendment_row"])
        after = wh.scalar("SELECT COUNT(*) FROM int_current_trades")

        current = wh.current_trade(TRADE_ID)
        check(loaded == 49 and before == 49 and after == 50,
              f"Current-trade counts {loaded}/{before}/{after} != 49/49/50")
        check(int(current["trade_version"]) == 2, "Current T-1001 must be v2.")
        check(float(current["notional_amount"]) == 10_000_000, "Current notional must be 10M.")

        self.ctx["warehouse"] = wh
        return {
            "initial_batch_rows": loaded,
            "current_trades_before_amendment": before,
            "current_trades_after_amendment": after,
            "t1001_current_version": int(current["trade_version"]),
            "t1001_current_notional": float(current["notional_amount"]),
        }

    # GT-06
    def stage_reporting(self):
        wh = self.ctx["warehouse"]
        created = wh.run_simulated_reporting()
        replayed = wh.run_simulated_reporting()

        t1001 = wh.submissions(TRADE_ID)
        check(created == 50, f"Expected 50 submissions, got {created}")
        check(replayed == 0, f"Replay created {replayed} duplicate submissions")
        check(len(t1001) == 1 and t1001[0]["trade_version"] == 2,
              "T-1001 must have exactly one submission, for v2.")
        check(not any(s["trade_version"] == 1 for s in t1001),
              "Blocked v1 must never be submitted.")

        rejected = [s["submission_id"] for s in wh.submissions()
                    if s["reporting_status"] == "REJECTED"]
        return {
            "submissions_created": created,
            "submissions_created_on_replay": replayed,
            "t1001_submission_id": t1001[0]["submission_id"],
            "t1001_reporting_status": t1001[0]["reporting_status"],
            "simulated_rejections": rejected,
            "note": "Simulated outcomes are positional (every 10th trade_id), not rule-based.",
        }

    # GT-07
    def stage_dashboard(self):
        expected = json.loads(paths.EXPECTED_DASHBOARD.read_text(encoding="utf-8"))
        k = self.ctx["warehouse"].kpis(self.ctx["summary"])

        actual = {
            "total_trades": k["total_trades"],
            "total_gbp_notional_m": round(k["total_notional_gbp"] / 1e6, 1),
            "current_validation_pass_rate_pct": k["current_pass_rate_pct"],
            "initial_quarantine_rate_pct": k["initial_quarantine_rate_pct"],
            "simulated_reject_rate_pct": k["simulated_reject_rate_pct"],
            "no_amendment_rate_pct": k["no_amendment_rate_pct"],
            "status_distribution": k["status_distribution"],
            # Power BI rounds half away from zero (106.5 -> 107); Python's
            # round() would give 106, so round explicitly.
            "counterparty_notional_m": {
                cp: round_half_up(v / 1e6) for cp, v in k["counterparty_notional_gbp"].items()
            },
            "t1001_original_notional_m": 100,
            "t1001_corrected_notional_m": round(
                self.ctx["warehouse"].current_trade(TRADE_ID)["notional_amount"] / 1e6
            ),
        }

        diffs = {
            key: {"dashboard": expected["kpis"][key], "sql": actual[key]}
            for key in expected["kpis"] if expected["kpis"][key] != actual[key]
        }
        check(not diffs, f"Dashboard does not reconcile: {diffs}")
        check(k["duplicate_trade_versions"] == [], "Duplicate trade/version rows found.")
        check(k["current_rows"] == k["total_trades"], "Amended versions double-counted.")

        return {"reconciled_kpis": len(expected["kpis"]), "values": actual,
                "dashboard_source": expected["source"]}

    # GT-08
    def stage_prediction(self):
        api = components.phase6_api()
        from fastapi.testclient import TestClient
        client = TestClient(api.app)
        prepare = __import__("assistant.prediction_client",
                             fromlist=["prepare_trade_features"]).prepare_trade_features

        health = client.get("/health").json()
        registry = json.loads(paths.MODEL_REGISTRY.read_text(encoding="utf-8"))
        approved = registry["versions"][registry["current"]]
        check(health["model_version"] == registry["current"], "Unexpected model version served.")
        check(health["model_sha256"] == approved["sha256"], "Served model checksum differs from registry.")

        phase5 = pd.read_csv(paths.PHASE5_T1001_PREDICTIONS)
        scores = {}
        for version, row in (
            (1, self.ctx["trades"][self.ctx["trades"]["trade_id"] == TRADE_ID].iloc[0]),
            (2, self.ctx["amended"].iloc[0]),
        ):
            features = prepare(row.to_dict())
            base = {k: features[k] for k in ("trade_id", "notional_amount", "currency",
                                              "product_type", "counterparty_id")}
            from_dates = client.post("/predict", json={**base, "tenor_years": features["tenor_years"]}).json()
            tenor_10 = client.post("/predict", json={**base, "tenor_years": 10}).json()
            recorded = float(phase5.loc[phase5["trade_version"] == version, "risk_probability"].iloc[0])

            check(abs(tenor_10["risk_score"] - recorded) <= 1e-6,
                  f"v{version} score {tenor_10['risk_score']} != Phase 5 {recorded}")

            scores[f"v{version}"] = {
                "notional": float(row["notional_amount"]),
                "tenor_from_dates": round(features["tenor_years"], 5),
                "risk_score_tenor_from_dates": from_dates["risk_score"],
                "risk_band_tenor_from_dates": from_dates["risk_band"],
                "risk_score_tenor_10": tenor_10["risk_score"],
                "phase5_recorded_score": round(recorded, 6),
            }

        self.ctx["predict_fn"] = components.predict_via_client(client)
        return {
            "model_name": health["model_name"],
            "model_version": health["model_version"],
            "model_sha256": health["model_sha256"],
            "threshold": approved["threshold"],
            "scores": scores,
        }

    # GT-09
    def stage_assistant(self):
        ops = components.assistant()
        wh = self.ctx["warehouse"]

        # The assistant reads a curated export, as it did from Snowflake.
        curated_file = self.workdir / "assistant_curated_export.csv"
        export = pd.DataFrame(wh.rows(
            "SELECT * FROM trades_validated WHERE trade_id = ?", (TRADE_ID,)))
        export.columns = [c.upper() for c in export.columns]
        export.to_csv(curated_file, index=False)

        before = components.snapshot_tree(self.sandbox)
        llm = None if self.live_llm else TemplateLLM()
        kwargs = {} if llm is None else {"llm_fn": llm}

        result = ops.answer_question(
            "Why was T-1001 blocked, and is the current version eligible for reporting?",
            backup_dir=self.ctx["batch"]["quarantine_root"],
            curated_file=curated_file,
            retriever=components.retriever(),
            predict_fn=self.ctx["predict_fn"],
            **kwargs,
        )
        after = components.snapshot_tree(self.sandbox)

        check(result["status"] == "success", f"Assistant failed: {result.get('message')}")
        pack = result["evidence_pack"]
        validation_part, model_part = pack.split("== MODEL RISK")
        check('"validation_status": "BLOCK"' in validation_part, "v1 BLOCK missing from evidence.")
        check('"validation_status": "PASS"' in validation_part, "v2 PASS missing from evidence.")
        check("DEMO_NOTIONAL_MISMATCH" in validation_part, "Rule ID missing from evidence.")
        check("risk_score" not in validation_part, "Model score leaked into validation evidence.")
        check(result["model_risk"]["scored_version"] == 2, "Assistant must score the current version.")
        check(result["unknown_citations"] == [], f"Invented citations: {result['unknown_citations']}")
        check(any(c.startswith("KB-") for c in result["citations_used"]), "No knowledge note cited.")
        check(before == after, "Assistant modified stored trade data.")

        (self.workdir / "assistant_answer.md").write_text(
            f"# Assistant answer ({'live LLM' if self.live_llm else TemplateLLM.name})\n\n"
            f"**Question:** {result['question']}\n\n{result['answer']}\n\n"
            f"## Citation check\n\n```json\n"
            f"{json.dumps({k: result[k] for k in ('citations_used', 'unknown_citations', 'warnings')}, indent=2)}"
            f"\n```\n\n## Evidence pack sent to the LLM\n\n```text\n{pack}\n```\n",
            encoding="utf-8",
        )

        return {
            "llm": "live" if self.live_llm else TemplateLLM.name,
            "citations_used": result["citations_used"],
            "unknown_citations": result["unknown_citations"],
            "warnings": result["warnings"],
            "kb_sources": result["kb_sources"],
            "model_risk_scored_version": result["model_risk"]["scored_version"],
            "model_risk_score": result["model_risk"]["risk_score"],
            "files_checked_unchanged": len(before),
        }


# Reporting
def write_report(result, out_dir, workdir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "golden_thread_run.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8")

    for name in ("assistant_answer.md", "phase3_batch_log.txt"):
        source = Path(workdir) / name
        if source.exists():
            (out_dir / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    lines = [
        "# T-1001 Golden Thread — Run Report",
        "",
        f"- **Overall:** {result['status']}",
        f"- **Run at (UTC):** {result['run_at_utc']}",
        f"- **Total runtime:** {result['total_seconds']} s",
        f"- **LLM mode:** {result['llm_mode']}",
        f"- **Environment:** Python {result['environment']['python']} · {result['environment']['platform']}",
        "",
        "| Stage | Name | Component | Status | Seconds |",
        "| --- | --- | --- | --- | --- |",
    ]
    for s in result["stages"]:
        lines.append(f"| {s['id']} | {s['name']} | {s['component']} | {s['status']} | {s.get('duration_seconds', '')} |")

    for s in result["stages"]:
        lines += ["", f"## {s['id']} — {s['name']}", ""]
        if s["status"] == "PASS":
            lines += ["```json", json.dumps(s["facts"], indent=2, default=str), "```"]
        else:
            lines.append(f"**{s['status']}** — {s.get('detail', '')}")

    (out_dir / "golden_thread_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the T-1001 golden thread.")
    parser.add_argument("--out", default=str(paths.EVIDENCE_DIR / "golden_thread"))
    parser.add_argument("--workdir", help="Keep the sandbox here instead of a temp dir.")
    parser.add_argument("--live-llm", action="store_true",
                        help="Use the real LLM (needs EURI_API_KEY).")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(args.workdir or tmp)
        workdir.mkdir(parents=True, exist_ok=True)
        result = GoldenThread(workdir, live_llm=args.live_llm).run()
        write_report(result, args.out, workdir)

    for s in result["stages"]:
        print(f"{s['id']}  {s['status']:<7} {s['name']}"
              + (f"  -> {s['detail']}" if s.get("detail") else ""))
    print(f"\nGOLDEN THREAD: {result['status']} in {result['total_seconds']}s")
    print(f"Evidence: {args.out}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
