"""FR-010 prediction and AI investigation, plus model rollback."""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from nbit import components, paths
from nbit.golden_thread import TemplateLLM

REGISTRY = json.loads(paths.MODEL_REGISTRY.read_text(encoding="utf-8"))
KNOWN_GOOD = REGISTRY["versions"][REGISTRY["current"]]

VALID_TRADE = {
    "trade_id": "T-1001", "notional_amount": 10_000_000, "tenor_years": 10,
    "currency": "GBP", "product_type": "GBP_IRS", "counterparty_id": "CP-004",
}


@pytest.fixture
def default_api():
    api = components.phase6_api()
    yield api
    components.phase6_api()  # always leave the known-good model loaded


# Prediction
@pytest.mark.tc("TC-AI-001")
def test_health_identifies_the_served_model(default_api):
    health = TestClient(default_api.app).get("/health").json()

    assert health["status"] == "healthy"
    assert health["model_version"] == REGISTRY["current"]
    assert health["model_sha256"] == KNOWN_GOOD["sha256"]


@pytest.mark.tc("TC-AI-002")
def test_t1001_scores_come_from_the_trained_model(stage):
    scores = stage("GT-08")["scores"]

    for version in ("v1", "v2"):
        s = scores[version]
        assert s["risk_score_tenor_10"] == pytest.approx(s["phase5_recorded_score"], abs=1e-6)
        assert 0 <= s["risk_score_tenor_from_dates"] <= 1

    # Same trade and model, different notional -> a genuinely different score.
    assert scores["v1"]["risk_band_tenor_from_dates"] == "Flagged"
    assert scores["v2"]["risk_band_tenor_from_dates"] == "Not Flagged"


@pytest.mark.tc("TC-AI-003")
def test_prediction_inputs_exclude_outcome_information(default_api):
    features = default_api.metadata["features"]
    for leaked in ("simulated_rejected", "reporting_status", "rejection_reason",
                   "validation_status", "detected_rules"):
        assert leaked not in features

    client = TestClient(default_api.app)
    response = client.post("/predict", json={**VALID_TRADE, "reporting_status": "REJECTED"})
    assert response.status_code == 422


# Assistant
@pytest.mark.tc("TC-AI-004")
def test_assistant_answer_is_grounded_in_retrieved_evidence(stage):
    facts = stage("GT-09")

    assert facts["unknown_citations"] == []
    assert facts["warnings"] == []
    assert any(c.startswith("QUARANTINE BATCH-") for c in facts["citations_used"])
    assert "CURATED T-1001 v2" in facts["citations_used"]
    assert any(c.startswith("KB-001") for c in facts["citations_used"])
    assert facts["kb_sources"][0] == "KB_001_Notional_Validation.md#Example: T-1001"


@pytest.mark.tc("TC-AI-005")
def test_assistant_cannot_change_trade_data(stage):
    # GT-09 snapshots every stored file before and after answering.
    assert stage("GT-09")["files_checked_unchanged"] >= 6


@pytest.mark.tc("TC-AI-005")
def test_assistant_exposes_no_write_operations():
    ops = components.assistant()
    public = {name for name in dir(ops) if not name.startswith("_")}
    for forbidden in ("approve", "amend", "cancel", "submit", "update_trade", "write"):
        assert not any(forbidden in name.lower() for name in public), forbidden


@pytest.mark.tc("TC-AI-006")
def test_unknown_trade_is_reported_as_missing_evidence(golden):
    ops = components.assistant()
    llm = TemplateLLM()
    result = ops.answer_question(
        "Why was T-9999 blocked?",
        backup_dir=golden.ctx["batch"]["quarantine_root"],
        curated_file=golden.workdir / "assistant_curated_export.csv",
        retriever=components.retriever(), llm_fn=llm,
        predict_fn=lambda trade: pytest.fail("Nothing should be scored"),
    )
    assert "NOT AVAILABLE: No trade records found for T-9999" in result["evidence_pack"]
    assert result["model_risk"]["status"] == "unavailable"


@pytest.mark.tc("TC-AI-006", "TC-NFR-005")
def test_prediction_outage_degrades_to_stated_gap(golden):
    ops = components.assistant()
    down = lambda trade: {"status": "error", "message": "Cannot connect to the prediction API."}
    result = ops.answer_question(
        "Why was T-1001 blocked?",
        backup_dir=golden.ctx["batch"]["quarantine_root"],
        curated_file=golden.workdir / "assistant_curated_export.csv",
        retriever=components.retriever(), llm_fn=TemplateLLM(), predict_fn=down,
    )
    assert result["status"] == "success"
    assert "NOT AVAILABLE: Cannot connect to the prediction API." in result["evidence_pack"]


@pytest.mark.tc("TC-AI-006")
def test_invented_citation_is_flagged():
    ops = components.assistant()
    check = ops.check_citations("Blocked per [KB-009 v9 - Invented Policy].",
                                allowed={"KB-001 v1.1 - Purpose"}, kb_results=[{}])
    assert check["unknown_citations"] == ["KB-009 v9 - Invented Policy"]


# Operations: rollback to a known model version
@pytest.mark.tc("TC-OPS-001")
def test_rollback_restores_known_good_model(tmp_path, default_api):
    # A candidate release (same weights, new version label) is deployed...
    candidate = tmp_path / "model_1.1.0-candidate"
    shutil.copytree(paths.MODEL_DIR, candidate)
    meta_path = candidate / "model_metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["model_version"] = "1.1.0-candidate"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    served = TestClient(components.phase6_api(candidate).app).get("/health").json()
    assert served["model_version"] == "1.1.0-candidate"

    # ...and rolled back by pointing at the registered version with its checksum pinned.
    rolled_back = components.phase6_api(paths.MODEL_DIR, expected_sha256=KNOWN_GOOD["sha256"])
    health = TestClient(rolled_back.app).get("/health").json()

    assert health["model_version"] == REGISTRY["current"]
    assert health["model_sha256"] == KNOWN_GOOD["sha256"]


@pytest.mark.tc("TC-OPS-001")
def test_api_refuses_to_start_with_unexpected_model(default_api):
    with pytest.raises(RuntimeError, match="Model checksum mismatch"):
        components.phase6_api(paths.MODEL_DIR, expected_sha256="0" * 64)
