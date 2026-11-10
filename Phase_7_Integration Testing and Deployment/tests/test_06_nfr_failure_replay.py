"""NFR-001 performance, NFR-004 auditability, NFR-005 safe failure."""

import json
import time

import pytest

from nbit import components
from nbit.audit_trail import build_trail, missing_attributes


@pytest.mark.tc("TC-NFR-001")
def test_50_trade_batch_processes_within_60_seconds(tmp_path):
    sandbox = components.seed_sandbox(tmp_path / "storage")
    started = time.perf_counter()
    components.run_phase3_batch(sandbox)
    elapsed = time.perf_counter() - started

    assert components.find_batch(sandbox)["success"].exists()
    assert elapsed <= 60, f"{elapsed:.2f}s"


@pytest.mark.tc("TC-NFR-004")
def test_t1001_lifecycle_trail_is_complete(golden):
    trail = build_trail(golden)

    assert missing_attributes(trail) == []
    assert [e["event_type"] for e in trail] == [
        "CAPTURED", "VALIDATED", "AMENDMENT_APPROVED",
        "AMENDED", "REVALIDATED", "REPORTED_SIMULATED",
    ]
    assert {e["trade_version"] for e in trail} == {1, 2}
    assert len({e["event_id"] for e in trail}) == len(trail)


# Fault injection on the published batch
@pytest.mark.tc("TC-NFR-005")
def test_corrupted_output_is_detected_on_replay(make_batch):
    sandbox, batch, _ = make_batch()
    curated = batch["curated"]
    curated.write_bytes(curated.read_bytes().replace(b"CP-002", b"CP-999", 1))
    tampered = curated.read_bytes()

    with pytest.raises(RuntimeError, match="SHA-256 mismatch|File size mismatch"):
        components.run_phase3_batch(sandbox)

    assert curated.read_bytes() == tampered  # left in place for investigation


@pytest.mark.tc("TC-NFR-005")
def test_partial_batch_is_not_overwritten(make_batch):
    sandbox, batch, _ = make_batch()
    batch["success"].unlink()        # simulate a crash before the completion marker
    batch["checksums"].unlink()
    before = components.snapshot_tree(sandbox)

    with pytest.raises(RuntimeError, match="Partial batch detected"):
        components.run_phase3_batch(sandbox)

    assert components.snapshot_tree(sandbox) == before


@pytest.mark.tc("TC-NFR-005")
def test_blocked_trade_keeps_its_source_reference(golden):
    import pandas as pd
    row = pd.read_csv(golden.ctx["batch"]["quarantine"]).iloc[0]

    assert row["source_trade_ref"] == "OMS-1001"
    assert row["source_file"] == "raw/trades/sample_trades.csv"
    assert len(row["source_checksum_sha256"]) == 64
    assert row["validation_run_id"].startswith("VAL-")
