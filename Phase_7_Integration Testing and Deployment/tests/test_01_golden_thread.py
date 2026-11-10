"""GT-001: the complete T-1001 lifecycle runs across every phase."""

import pytest


@pytest.mark.tc("TC-GT-001")
def test_golden_thread_every_stage_passes(golden):
    failed = [(s["id"], s.get("detail")) for s in golden.result["stages"]
              if s["status"] != "PASS"]
    assert not failed, failed
    assert [s["id"] for s in golden.result["stages"]] == [
        f"GT-0{i}" for i in range(1, 10)
    ]


@pytest.mark.tc("TC-GT-001")
def test_golden_thread_tells_one_consistent_story(stage):
    capture = stage("GT-01")
    validation = stage("GT-02")
    amendment = stage("GT-03")
    revalidation = stage("GT-04")
    reporting = stage("GT-06")
    prediction = stage("GT-08")
    assistant = stage("GT-09")

    # Original capture -> exception
    assert capture["t1001_captured_notional"] == 100_000_000
    assert validation["exception"]["rule_id"] == "DEMO_NOTIONAL_MISMATCH"

    # Exception -> approved amendment -> revalidation
    assert amendment["new_version"] == 2
    assert amendment["corrected_notional"] == capture["t1001_confirmed_notional"]
    assert revalidation["approval_reference_linked"] == amendment["approval_reference"]
    assert revalidation["v2_revalidation_rules"] == []

    # Revalidation -> simulated reporting on the corrected version only
    assert reporting["t1001_submission_id"] == "SIM-T-1001-V2"

    # Prediction and assistant both describe the current version
    assert assistant["model_risk_scored_version"] == 2
    assert assistant["model_risk_score"] == (
        prediction["scores"]["v2"]["risk_score_tenor_from_dates"]
    )
    assert f"QUARANTINE {validation['batch_id']}" in assistant["citations_used"]
