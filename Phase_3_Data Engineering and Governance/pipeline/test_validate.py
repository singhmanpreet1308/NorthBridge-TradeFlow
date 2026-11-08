import pandas as pd
import pytest
import json
import hashlib
from unittest.mock import MagicMock, patch

from validate import verify_output_checksums
from validate import validate_trade
from validate import reconcile_confirmation


def test_negative_notional():
    """A negative notional must trigger DQ-004."""

    trade = pd.Series({
        "trade_id": "TEST-001",
        "counterparty_id": "CP-001",
        "floating_rate_index": "SONIA",
        "notional_amount": -5000000,
        "currency": "GBP",
        "effective_date": "2026-09-23",
        "maturity_date": "2031-09-23",
        "fixed_rate": 0.035,
        "pay_receive_fixed": "PAY"
    })

    detected_rules = validate_trade(trade)

    assert "DQ-004" in detected_rules



@pytest.mark.parametrize(
    "field,invalid_value,expected_rule",
    [
        ("trade_id", None, "DQ-001"),
        ("counterparty_id", None, "DQ-009"),
        ("floating_rate_index", None, "DQ-009"),
        ("notional_amount", -5000000, "DQ-004"),
        ("notional_amount", 0, "DQ-004"),
        ("currency", "USD", "DQ-005"),
        ("maturity_date", "2020-01-01", "DQ-006"),
        ("fixed_rate", 1.25, "DQ-007"),
        ("pay_receive_fixed", "INVALID", "DQ-008"),
    ]
)
def test_trade_validation_rules(
    field, invalid_value, expected_rule
):
    """Verify each invalid field triggers its expected DQ rule."""

    valid_trade = {
        "trade_id": "TEST-001",
        "counterparty_id": "CP-001",
        "floating_rate_index": "SONIA",
        "notional_amount": 10000000,
        "currency": "GBP",
        "effective_date": "2026-09-23",
        "maturity_date": "2031-09-23",
        "fixed_rate": 0.035,
        "pay_receive_fixed": "PAY"
    }

    valid_trade[field] = invalid_value

    detected_rules = validate_trade(pd.Series(valid_trade))

    assert expected_rule in detected_rules, (
        f"Expected {expected_rule}, got {detected_rules}"
    )

def test_notional_mismatch():
    """T-1001: £100M captured vs £10M confirmed."""

    trade = pd.Series({
        "trade_id": "T-1001",
        "notional_amount": 100000000
    })

    confirmations = pd.DataFrame([{
        "trade_id": "T-1001",
        "notional_amount": 10000000
    }])

    detected_rules = reconcile_confirmation(
        trade, confirmations
    )

    assert "DEMO_NOTIONAL_MISMATCH" in detected_rules


def test_matching_notional():
    """Matching notionals must not trigger a mismatch."""

    trade = pd.Series({
        "trade_id": "T-1002",
        "notional_amount": 10000000
    })

    confirmations = pd.DataFrame([{
        "trade_id": "T-1002",
        "notional_amount": 10000000
    }])

    detected_rules = reconcile_confirmation(
        trade, confirmations
    )

    assert detected_rules == []


def test_missing_trade_id_reconciliation():
    """Missing trade ID cannot be reconciled."""

    trade = pd.Series({
        "trade_id": None,
        "notional_amount": 10000000
    })

    confirmations = pd.DataFrame([{
        "trade_id": "T-1001",
        "notional_amount": 10000000
    }])

    detected_rules = reconcile_confirmation(
        trade, confirmations
    )

    assert detected_rules == []


def test_missing_confirmation():
    """A trade without a matching confirmation must be flagged."""

    trade = pd.Series({
        "trade_id": "TEST-999",
        "notional_amount": 10000000
    })

    confirmations = pd.DataFrame([{
        "trade_id": "T-1001",
        "notional_amount": 10000000
    }])

    errors = reconcile_confirmation(trade, confirmations)

    assert "RECON_MISSING_CONFIRMATION" in errors


def test_duplicate_confirmation():
    """Multiple confirmations for one trade must be flagged."""

    trade = pd.Series({
        "trade_id": "T-1001",
        "notional_amount": 10000000
    })

    confirmations = pd.DataFrame([
        {
            "trade_id": "T-1001",
            "notional_amount": 10000000
        },
        {
            "trade_id": "T-1001",
            "notional_amount": 10000000
        }
    ])

    errors = reconcile_confirmation(trade, confirmations)

    assert "RECON_DUPLICATE_CONFIRMATION" in errors


def test_checksum_detects_corrupted_file():
    """A modified stored file must fail checksum verification."""

    batch_id = "BATCH-TEST-001"
    file_path = "curated/trades/test/validated_trades.csv"

    original_content = b"trade_id,notional\nT-1001,10000000"
    corrupted_content = b"trade_id,notional\nT-1001,90000000"

    output_paths = {
        "Curated": file_path
    }

    manifest = {
        "batch_id": batch_id,
        "outputs": {
            "curated": {
                "path": file_path,
                "size_bytes": len(original_content),
                "sha256": hashlib.sha256(
                    original_content
                ).hexdigest()
            }
        }
    }

    mock_filesystem = MagicMock()

    def mock_file_client(path):
        client = MagicMock()

        if path.endswith("output_checksums.json"):
            content = json.dumps(manifest).encode("utf-8")
        elif path == file_path:
            content = corrupted_content
        else:
            raise AssertionError(f"Unexpected Azure path: {path}")

        client.download_file.return_value.readall.return_value = content
        return client

    mock_filesystem.get_file_client.side_effect = mock_file_client

    with (
        patch("validate.filesystem", mock_filesystem),
        patch("validate.check_adls_file_exists", return_value=True)
    ):
        with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
            verify_output_checksums(
                batch_id,
                output_paths
            )


def test_missing_checksum_manifest():
    """A missing checksum manifest must stop verification."""

    batch_id = "BATCH-TEST-002"

    output_paths = {
        "Curated": "curated/trades/test/validated_trades.csv"
    }

    with patch(
        "validate.check_adls_file_exists",
        return_value=False
    ):
        with pytest.raises(
            RuntimeError,
            match="Checksum manifest missing"
        ):
            verify_output_checksums(
                batch_id,
                output_paths
            )

def test_checksum_verification_success():
    """Valid stored content must pass checksum verification."""

    batch_id = "BATCH-TEST-003"
    file_path = "curated/trades/test/validated_trades.csv"

    file_content = b"trade_id,notional\nT-1001,10000000"

    output_paths = {
        "Curated": file_path
    }

    manifest = {
        "batch_id": batch_id,
        "outputs": {
            "curated": {
                "path": file_path,
                "size_bytes": len(file_content),
                "sha256": hashlib.sha256(
                    file_content
                ).hexdigest()
            }
        }
    }

    mock_filesystem = MagicMock()

    def mock_file_client(path):
        client = MagicMock()

        if path.endswith("output_checksums.json"):
            content = json.dumps(manifest).encode("utf-8")
        elif path == file_path:
            content = file_content
        else:
            raise AssertionError(f"Unexpected path: {path}")

        client.download_file.return_value.readall.return_value = content
        return client

    mock_filesystem.get_file_client.side_effect = mock_file_client

    with (
        patch("validate.filesystem", mock_filesystem),
        patch("validate.check_adls_file_exists", return_value=True)
    ):
        result = verify_output_checksums(
            batch_id,
            output_paths
        )

    assert result is True


def test_checksum_rejects_wrong_batch_id():
    """A manifest from another batch must be rejected."""

    manifest = {
        "batch_id": "BATCH-WRONG",
        "outputs": {}
    }

    mock_filesystem = MagicMock()
    mock_filesystem.get_file_client.return_value \
        .download_file.return_value \
        .readall.return_value = json.dumps(manifest).encode()

    with (
        patch("validate.filesystem", mock_filesystem),
        patch("validate.check_adls_file_exists", return_value=True)
    ):
        with pytest.raises(
            RuntimeError,
            match="Checksum manifest batch ID mismatch"
        ):
            verify_output_checksums(
                "BATCH-EXPECTED",
                {"Curated": "curated/trades/test.csv"}
            )


def test_checksum_rejects_wrong_file_size():
    """Stored file size must match the checksum manifest."""

    batch_id = "BATCH-TEST-004"
    file_path = "curated/trades/test.csv"

    original_content = b"original content"
    modified_content = b"modified content with extra bytes"

    manifest = {
        "batch_id": batch_id,
        "outputs": {
            "curated": {
                "path": file_path,
                "size_bytes": len(original_content),
                "sha256": hashlib.sha256(
                    original_content
                ).hexdigest()
            }
        }
    }

    mock_filesystem = MagicMock()

    def mock_file_client(path):
        client = MagicMock()

        if path.endswith("output_checksums.json"):
            content = json.dumps(manifest).encode()
        elif path == file_path:
            content = modified_content
        else:
            raise AssertionError(f"Unexpected path: {path}")

        client.download_file.return_value.readall.return_value = content
        return client

    mock_filesystem.get_file_client.side_effect = mock_file_client

    with (
        patch("validate.filesystem", mock_filesystem),
        patch("validate.check_adls_file_exists", return_value=True)
    ):
        with pytest.raises(
            RuntimeError,
            match="File size mismatch"
        ):
            verify_output_checksums(
                batch_id,
                {"Curated": file_path}
            )
