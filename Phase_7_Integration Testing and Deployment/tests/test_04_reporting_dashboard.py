"""FR-008 simulated reporting and FR-009 dashboard reconciliation."""

import json
import socket

import pandas as pd
import pytest

from nbit import paths


# FR-008
@pytest.mark.tc("TC-RPT-001")
def test_only_current_eligible_versions_are_submitted(golden):
    wh = golden.ctx["warehouse"]
    current = {r["trade_id"]: r["trade_version"]
               for r in wh.rows("SELECT trade_id, trade_version FROM int_current_trades")}
    submissions = wh.submissions()

    assert len(submissions) == len(current) == 50
    for s in submissions:
        assert s["trade_version"] == current[s["trade_id"]]
        assert s["submission_id"] == f"SIM-{s['trade_id']}-V{s['trade_version']}"

    assert [s["submission_id"] for s in wh.submissions("T-1001")] == ["SIM-T-1001-V2"]


@pytest.mark.tc("TC-RPT-002")
def test_reporting_outcomes_are_recorded_separately_from_validation(golden):
    wh = golden.ctx["warehouse"]
    rejected = wh.rows("""
        SELECT r.trade_id, r.rejection_reason, t.validation_status
        FROM simulated_reporting_outcomes r
        JOIN int_current_trades t
          ON t.trade_id = r.trade_id AND t.trade_version = r.trade_version
        WHERE r.reporting_status = 'REJECTED'
    """)

    assert wh.scalar("SELECT COUNT(*) FROM simulated_reporting_outcomes "
                     "WHERE reporting_status = 'ACCEPTED'") == 45
    assert len(rejected) == 5
    # Internally valid trades can still be (simulated) rejected downstream.
    assert {r["validation_status"] for r in rejected} == {"PASS"}
    assert {r["rejection_reason"] for r in rejected} == {"DEMO_REPORT_REJECT"}


@pytest.mark.tc("TC-RPT-003", "TC-NFR-002")
def test_reporting_replay_creates_no_duplicate_submissions(golden):
    wh = golden.ctx["warehouse"]
    assert wh.run_simulated_reporting() == 0
    assert wh.scalar("SELECT COUNT(DISTINCT submission_id) FROM simulated_reporting_outcomes") == 50
    assert wh.scalar("SELECT COUNT(*) FROM simulated_reporting_outcomes") == 50


@pytest.mark.tc("TC-RPT-004")
def test_simulated_reporting_makes_no_network_calls(batch_warehouse, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Simulated reporting attempted a network connection")

    monkeypatch.setattr(socket, "socket", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)

    wh, _ = batch_warehouse
    assert wh.run_simulated_reporting() == 49


# FR-009
@pytest.mark.tc("TC-BI-001")
def test_headline_kpis_reconcile_with_dashboard(stage):
    expected = json.loads(paths.EXPECTED_DASHBOARD.read_text(encoding="utf-8"))["kpis"]
    actual = stage("GT-07")["values"]

    for key in ("total_trades", "total_gbp_notional_m", "current_validation_pass_rate_pct",
                "initial_quarantine_rate_pct", "simulated_reject_rate_pct",
                "no_amendment_rate_pct", "t1001_original_notional_m",
                "t1001_corrected_notional_m"):
        assert actual[key] == expected[key], key


@pytest.mark.tc("TC-BI-002")
def test_breakdowns_reconcile_with_dashboard(stage):
    expected = json.loads(paths.EXPECTED_DASHBOARD.read_text(encoding="utf-8"))["kpis"]
    actual = stage("GT-07")["values"]

    assert actual["status_distribution"] == expected["status_distribution"]
    assert actual["counterparty_notional_m"] == expected["counterparty_notional_m"]


@pytest.mark.tc("TC-BI-003")
def test_amended_versions_are_not_double_counted(golden, raw_trades):
    k = golden.ctx["warehouse"].kpis(golden.ctx["summary"])

    assert k["current_rows"] == k["total_trades"] == 50
    assert k["duplicate_trade_versions"] == []
    # Raw total minus the GBP 90M T-1001 correction, counted once.
    assert k["total_notional_gbp"] == raw_trades["notional_amount"].sum() - 90_000_000
