
import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]

source_path = (
    PROJECT_ROOT / "Phase_3_Data Engineering and Governance"
    / "azure_backup" / "raw" / "trades" / "sample_trades.csv"
)
approval_path = BASE_DIR / "T1001_Approval.json"
output_path = BASE_DIR / "T1001_v2.csv"


class AmendmentConflictError(ValueError):
    """The approval refers to a version that is no longer current."""


def build_amendment(trades, approval, now=None):
    """Return the approved new trade version as a one-row DataFrame.

    The original version is never modified: the new version is a copy
    with only the approved fields changed.
    """

    # Confirm approval and original trade.
    if approval.get("approval_status") != "APPROVED":
        raise ValueError("Amendment has not been approved.")

    trade_id = approval["trade_id"]
    original_version = int(approval["original_version"])
    amended_version = int(approval["amended_version"])

    versions = trades.loc[trades["trade_id"] == trade_id, "trade_version"]

    # Stale-version protection: the approval must target the latest version.
    if len(versions) and int(versions.max()) != original_version:
        raise AmendmentConflictError(
            f"Stale amendment: approval targets v{original_version}, "
            f"current version is v{int(versions.max())}."
        )

    if amended_version != original_version + 1:
        raise ValueError("Amended version must be original version + 1.")

    original = trades.loc[
        (trades["trade_id"] == trade_id)
        & (trades["trade_version"] == original_version)
    ]

    if len(original) != 1:
        raise ValueError(
            f"Expected exactly one {trade_id} version {original_version}."
        )

    # Preserve original fields.
    amended = original.copy()

    # Apply approved correction.
    amended.loc[:, "trade_version"] = amended_version
    amended.loc[:, "notional_amount"] = float(approval["corrected_notional_gbp"])
    amended.loc[:, "trade_status"] = "AMENDED"
    amended["amendment_reason"] = amended["amendment_reason"].astype("string")
    amended["amendment_reason"] = approval["amendment_reason"]
    amended.loc[:, "record_timestamp"] = (
        now or datetime.now(timezone.utc)
    ).isoformat()

    return amended


def main():
    # Read source trades and approval evidence.
    trades = pd.read_csv(source_path)
    approval = json.loads(approval_path.read_text(encoding="utf-8"))

    amended = build_amendment(trades, approval)

    # Never overwrite an existing amendment.
    if output_path.exists():
        raise FileExistsError(f"Amendment already exists: {output_path}")

    amended.to_csv(output_path, index=False)

    print("AMENDMENT_CREATED")
    print(amended[[
        "trade_id",
        "trade_version",
        "notional_amount",
        "trade_status",
        "amendment_reason"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
