"""Reconstruct the T-1001 lifecycle audit trail from component artefacts.

There is no single event store in the implemented system: each component
writes its own evidence (source record, quarantine row, approval JSON,
amendment audit JSON, reporting row). NFR-004 asks for one attributable
trail, so this module assembles it and checks the mandatory attributes.
Anything it cannot find stays None and fails the completeness check.
"""

import json

import pandas as pd

from nbit import paths

MANDATORY = ["event_id", "trade_id", "trade_version", "event_type",
             "event_timestamp", "actor_id", "processing_run_id", "event_outcome"]


def build_trail(golden):
    ctx = golden.ctx
    v1 = ctx["trades"][ctx["trades"]["trade_id"] == "T-1001"].iloc[0]
    exception = pd.read_csv(ctx["batch"]["quarantine"]).iloc[0]
    approval = ctx["approval"]
    v2 = pd.read_csv(paths.AMENDMENT_SOURCE).iloc[0]
    audit = json.loads(paths.AMENDMENT_AUDIT.read_text(encoding="utf-8"))
    report = ctx["warehouse"].submissions("T-1001")[0]

    def event(n, version, kind, ts, actor, run, outcome, source, **extra):
        return {"event_id": f"EVT-T-1001-{n:02d}", "trade_id": "T-1001",
                "trade_version": version, "event_type": kind, "event_timestamp": ts,
                "actor_id": actor, "processing_run_id": run,
                "event_outcome": outcome, "evidence_source": source, **extra}

    return [
        event(1, 1, "CAPTURED", v1["capture_timestamp"], v1["created_by"],
              ctx["batch"]["batch_id"], "CAPTURED", "raw/trades/sample_trades.csv",
              notional=float(v1["notional_amount"])),
        event(2, 1, "VALIDATED", exception["validated_at_utc"], "pipeline.validate (policy 1.1)",
              exception["validation_run_id"], exception["validation_status"],
              "quarantine/trades/<batch>/blocked_trades.csv",
              rule_id=json.loads(exception["detected_rules"])[0]),
        event(3, 2, "AMENDMENT_APPROVED", approval["approval_timestamp_utc"],
              approval["approved_by"], approval["approval_reference"],
              approval["approval_status"], "amendments/T1001_Approval.json",
              reason=approval["amendment_reason"]),
        event(4, 2, "AMENDED", v2["record_timestamp"], "create_amendment.py",
              approval["approval_reference"], "AMENDED", "amendments/T1001_v2.csv",
              notional=float(v2["notional_amount"])),
        event(5, 2, "REVALIDATED", audit["validated_at_utc"], "validate_amendment.py",
              audit["validation_run_id"], audit["validation_status"],
              "amendments/validated_output/T1001_v2_audit.json"),
        event(6, 2, "REPORTED_SIMULATED", report["processed_at"], "simulated_reporting",
              report["submission_id"], report["reporting_status"],
              "simulated_reporting_outcomes"),
    ]


def missing_attributes(trail):
    return [(e["event_id"], f) for e in trail for f in MANDATORY
            if e.get(f) is None or (isinstance(e.get(f), float) and pd.isna(e[f]))
            or str(e.get(f)).strip() == ""]
