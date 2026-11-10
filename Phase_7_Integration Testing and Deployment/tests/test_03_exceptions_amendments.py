"""FR-004 exceptions, FR-005 approval, FR-006 versioning, FR-007 revalidation."""

import json

import pandas as pd
import pytest

from nbit import components
from nbit.warehouse import Warehouse


# FR-004 Exception management
@pytest.mark.tc("TC-EXC-001")
def test_exception_record_is_complete_and_attributable(golden):
    quarantine = pd.read_csv(golden.ctx["batch"]["quarantine"])
    record = quarantine[quarantine["trade_id"] == "T-1001"].iloc[0]

    for field in ("trade_id", "trade_version", "detected_rules", "validation_status",
                  "validation_run_id", "validated_at_utc", "source_file",
                  "source_checksum_sha256"):
        assert pd.notna(record[field]) and str(record[field]).strip(), field

    assert json.loads(record["detected_rules"]) == ["DEMO_NOTIONAL_MISMATCH"]
    assert record["validation_status"] == "BLOCK"
    # Responsible reviewer is recorded on the approval, not on the exception.
    assert golden.ctx["approval"]["approved_by"]


@pytest.mark.tc("TC-EXC-002", "TC-NFR-005")
def test_unresolved_exception_blocks_simulated_reporting(batch_warehouse):
    wh, _ = batch_warehouse
    wh.run_simulated_reporting()

    assert wh.submissions("T-1001") == []
    assert len(wh.submissions()) == 49


# FR-005 / FR-006 Approved amendment and versioning
@pytest.mark.tc("TC-AMD-001")
def test_approved_amendment_creates_version_2(raw_trades):
    create = components.phase4_create_amendment()
    amended = create.build_amendment(raw_trades, components.load_approval())

    assert len(amended) == 1
    row = amended.iloc[0]
    assert (row["trade_id"], int(row["trade_version"])) == ("T-1001", 2)
    assert float(row["notional_amount"]) == 10_000_000
    assert row["trade_status"] == "AMENDED"
    assert row["amendment_reason"] == "DEMO_NOTIONAL_MISMATCH"


@pytest.mark.tc("TC-AMD-002")
def test_rejected_amendment_creates_no_version(raw_trades):
    create = components.phase4_create_amendment()
    approval = {**components.load_approval(), "approval_status": "REJECTED"}
    before = raw_trades.copy()

    with pytest.raises(ValueError, match="not been approved"):
        create.build_amendment(raw_trades, approval)

    pd.testing.assert_frame_equal(raw_trades, before)


@pytest.mark.tc("TC-AMD-004", "TC-NFR-002")
def test_duplicate_amendment_load_is_rejected(golden, amendment_copy):
    ingest = components.phase4_ingest_amendments()
    wh = Warehouse()
    wh.load_curated_batch(golden.ctx["batch"]["curated"])

    columns, row = ingest.verify_batch(amendment_copy["csv"], amendment_copy["audit"],
                                       amendment_copy["approval"], amendment_copy["source"])
    wh.load_amendment(columns, row)
    rows_after_first = wh.scalar("SELECT COUNT(*) FROM trades_validated")

    with pytest.raises(ValueError, match="already exists"):
        wh.load_amendment(columns, row)

    assert wh.scalar("SELECT COUNT(*) FROM trades_validated") == rows_after_first == 50


@pytest.mark.tc("TC-AMD-005")
def test_stale_version_amendment_raises_conflict(raw_trades):
    create = components.phase4_create_amendment()
    approval = components.load_approval()

    # T-1001 already has v2, but the approval still targets v1.
    already_amended = create.build_amendment(raw_trades, approval)
    trades_with_v2 = pd.concat([raw_trades, already_amended], ignore_index=True)

    with pytest.raises(create.AmendmentConflictError, match="Stale amendment"):
        create.build_amendment(trades_with_v2, approval)


@pytest.mark.tc("TC-AMD-007", "TC-NFR-004")
def test_both_versions_remain_accessible(golden):
    quarantine = pd.read_csv(golden.ctx["batch"]["quarantine"])
    wh = golden.ctx["warehouse"]

    v1 = quarantine[quarantine["trade_id"] == "T-1001"].iloc[0]
    v2 = wh.rows("SELECT * FROM trades_validated WHERE trade_id = 'T-1001'")

    assert int(v1["trade_version"]) == 1 and float(v1["notional_amount"]) == 100_000_000
    assert len(v2) == 1 and int(v2[0]["trade_version"]) == 2
    assert wh.current_trade("T-1001")["trade_version"] == 2


# FR-007 Revalidation
@pytest.mark.tc("TC-AMD-006", "TC-NFR-005")
def test_failed_revalidation_keeps_reporting_blocked(raw_trades, confirmations, batch_warehouse):
    create = components.phase4_create_amendment()
    revalidate = components.phase4_validate_amendment().revalidate

    wrong = {**components.load_approval(), "corrected_notional_gbp": 20_000_000}
    amended = create.build_amendment(raw_trades, wrong)

    assert revalidate(amended.iloc[0], confirmations) == ["DEMO_NOTIONAL_MISMATCH"]

    # A failed revalidation produces no validated output, so nothing is loaded.
    wh, _ = batch_warehouse
    wh.run_simulated_reporting()
    assert wh.submissions("T-1001") == []


@pytest.mark.tc("TC-AMD-009")
def test_v2_is_evaluated_independently_of_v1(stage):
    facts = stage("GT-04")
    assert facts["v1_revalidation_rules"] == ["DEMO_NOTIONAL_MISMATCH"]
    assert facts["v2_revalidation_rules"] == []


# FR-005 approval evidence (and the partial NFR-003 control it provides)
@pytest.mark.tc("TC-AMD-008", "TC-NFR-003")
@pytest.mark.parametrize("tamper,message", [
    (lambda a: a.update(approval_status="PENDING"), "Approval verification failed"),
    (lambda a: a.update(approved_by=""), "Approval verification failed"),
    (lambda a: a.update(approval_reference="NB-FORGED-001"), "Approval verification failed"),
    (lambda a: a.update(corrected_notional_gbp=20_000_000), "Approved notional mismatch"),
])
def test_amendment_without_valid_approval_is_refused(amendment_copy, tamper, message):
    ingest = components.phase4_ingest_amendments()
    approval = json.loads(amendment_copy["approval"].read_text(encoding="utf-8"))
    tamper(approval)
    amendment_copy["approval"].write_text(json.dumps(approval), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        ingest.verify_batch(amendment_copy["csv"], amendment_copy["audit"],
                            amendment_copy["approval"], amendment_copy["source"])


@pytest.mark.tc("TC-AMD-008", "TC-NFR-005")
def test_amendment_source_edited_after_validation_is_refused(amendment_copy):
    ingest = components.phase4_ingest_amendments()
    source = amendment_copy["source"]
    source.write_bytes(source.read_bytes().replace(b"10000000.0", b"11000000.0"))

    with pytest.raises(ValueError, match="Source checksum mismatch"):
        ingest.verify_batch(amendment_copy["csv"], amendment_copy["audit"],
                            amendment_copy["approval"], source)
