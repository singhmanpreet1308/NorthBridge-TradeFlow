"""FR-001 capture, FR-002 validation, FR-003 confirmation checks."""

import json

import pandas as pd
import pytest

from nbit import components, paths

SOURCE_COLUMNS = [
    "trade_id", "trade_version", "source_system", "source_trade_ref",
    "capture_timestamp", "trade_date", "counterparty_id", "product_type",
    "currency", "notional_amount", "fixed_rate", "floating_rate_index",
    "pay_receive_fixed", "effective_date", "maturity_date",
    "payment_frequency", "trade_status", "amendment_reason", "created_by",
    "record_timestamp",
]


@pytest.mark.tc("TC-CAP-001")
def test_valid_trades_are_published_at_version_1_unmodified(golden, raw_trades):
    curated = pd.read_csv(golden.ctx["batch"]["curated"])

    assert len(curated) == 49
    assert set(curated["trade_version"]) == {1}

    # Every source field is carried through exactly.
    merged = curated[SOURCE_COLUMNS].merge(
        raw_trades, on=["trade_id", "trade_version"], suffixes=("", "_raw"))
    for column in SOURCE_COLUMNS[2:]:
        left = merged[column].fillna("").astype(str)
        right = merged[f"{column}_raw"].fillna("").astype(str)
        assert (left == right).all(), column


@pytest.mark.tc("TC-CAP-002")
def test_missing_mandatory_fields_produce_explicit_rule_ids(raw_trades):
    validate = components.phase3_validate()
    row = raw_trades[raw_trades["trade_id"] == "T-1002"].iloc[0].copy()

    row["counterparty_id"] = None
    assert "DQ-009" in validate.validate_trade(row)

    row = raw_trades[raw_trades["trade_id"] == "T-1002"].iloc[0].copy()
    row["trade_id"] = None
    assert "DQ-001" in validate.validate_trade(row)


@pytest.mark.tc("TC-CAP-003", "TC-NFR-002")
def test_replaying_the_same_batch_changes_nothing(make_batch):
    sandbox, batch, _ = make_batch()
    before = components.snapshot_tree(sandbox)

    log = components.run_phase3_batch(sandbox)

    assert "Batch status: SKIPPED" in log
    assert "All stored output checksums verified." in log
    assert components.snapshot_tree(sandbox) == before


@pytest.mark.tc("TC-CAP-004")
def test_conflicting_trade_id_fails_closed_without_publishing(tmp_path):
    """Design expects 'held for review'. The pipeline instead aborts the whole
    batch via its baseline-count control, so nothing is published. Safe, but
    it is a count check, not a dedicated conflict detector."""
    sandbox = components.seed_sandbox(tmp_path / "storage")
    path = sandbox / "raw" / "trades" / "sample_trades.csv"
    trades = pd.read_csv(path)
    conflict = trades[trades["trade_id"] == "T-1002"].copy()
    conflict["notional_amount"] = 99_000_000
    pd.concat([trades, conflict]).to_csv(path, index=False)

    with pytest.raises(Exception) as error:
        components.run_phase3_batch(sandbox)

    assert "Baseline validation counts changed" in str(error.value)
    assert not (sandbox / "curated" / "trades").exists()
    assert not (sandbox / "quarantine").exists()


@pytest.mark.tc("TC-CAP-005")
def test_t1001_original_notional_is_retained(golden):
    quarantine = pd.read_csv(golden.ctx["batch"]["quarantine"])
    t1001 = quarantine[quarantine["trade_id"] == "T-1001"].iloc[0]

    assert float(t1001["notional_amount"]) == 100_000_000
    assert int(t1001["trade_version"]) == 1

    # The raw capture file itself is untouched by processing.
    raw = golden.sandbox / "raw" / "trades" / "sample_trades.csv"
    manifest = json.loads(paths.FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    assert components.sha256_file(raw) == manifest["files"]["trades/sample_trades.csv"]["sha256"]


@pytest.mark.tc("TC-VAL-001")
def test_all_seeded_defects_are_detected(stage):
    assert stage("GT-02")["seeded_defects_detected"] == "10/10"

    validate = components.phase3_validate()
    reference = paths.RAW_FIXTURES / "reference"
    result = validate.verify_error_manifest(
        pd.read_csv(reference / "seeded_errors.csv"),
        pd.read_csv(paths.RAW_FIXTURES / "confirmations" / "independent_confirmations.csv"),
        pd.read_csv(reference / "seeded_error_manifest.csv"),
    )
    assert len(result) == 10
    assert (result["test_result"] == "PASS").all(), result.to_string()


@pytest.mark.tc("TC-VAL-002")
def test_t1001_notional_mismatch_detected_against_confirmation(stage):
    facts = stage("GT-02")
    assert facts["exception"]["rule_id"] == "DEMO_NOTIONAL_MISMATCH"
    assert stage("GT-01")["t1001_confirmed_notional"] == 10_000_000


@pytest.mark.tc("TC-VAL-003")
def test_missing_confirmation_is_unresolved_not_a_match(raw_trades, confirmations):
    validate = components.phase3_validate()
    row = raw_trades[raw_trades["trade_id"] == "T-1002"].iloc[0]
    without_t1002 = confirmations[confirmations["trade_id"] != "T-1002"]

    assert validate.validate_trade(row) == []
    assert validate.reconcile_confirmation(row, confirmations) == []
    assert validate.reconcile_confirmation(row, without_t1002) == [
        "RECON_MISSING_CONFIRMATION"
    ]


@pytest.mark.tc("TC-VAL-003", "TC-NFR-005")
def test_missing_confirmation_in_a_batch_fails_closed(tmp_path):
    """Finding: the batch has a hard-coded 49 PASS / 1 BLOCK control, so a new
    exception aborts the whole batch instead of quarantining one trade. Safe
    (nothing invalid is published) but not how a production batch should behave."""
    sandbox = components.seed_sandbox(tmp_path / "storage")
    path = sandbox / "raw" / "confirmations" / "independent_confirmations.csv"
    confirmations = pd.read_csv(path)
    confirmations[confirmations["trade_id"] != "T-1002"].to_csv(path, index=False)

    with pytest.raises(RuntimeError, match="Baseline validation counts changed"):
        components.run_phase3_batch(sandbox)

    assert not (sandbox / "curated" / "trades").exists()


@pytest.mark.tc("TC-VAL-004")
def test_batch_identity_reproduces_recorded_phase3_batch(stage):
    manifest = json.loads(paths.FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    assert stage("GT-02")["batch_id"] == manifest["recorded_batch_id"]
