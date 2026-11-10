
import os
import sys
from pathlib import Path
import pandas as pd
import json
import hashlib
import uuid
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Locate existing Phase 3 validation logic.
PHASE3_DIR = (
    PROJECT_ROOT.parent
    / "Phase_3_Data Engineering and Governance"
)

sys.path.insert(0, str(PHASE3_DIR))

# Revalidation reads local files only; never needs Azure credentials.
os.environ.setdefault("STORAGE_MODE", "local")

from pipeline.validate import (
    validate_trade,
    reconcile_confirmation
)


def revalidate(row, confirmations):
    """Apply the same Phase 3 rules used for the original capture."""
    errors = validate_trade(row)

    if "DQ-004" not in errors:
        errors += reconcile_confirmation(row, confirmations)

    return list(dict.fromkeys(errors))


def verify_approval(approval, trade_id="T-1001", amended_version=2,
                    approval_reference="NB-T1001-APP-001"):
    """Require documented approval evidence for this exact amendment."""
    if (
        approval.get("approval_status") != "APPROVED"
        or approval.get("trade_id") != trade_id
        or int(approval.get("amended_version", -1)) != amended_version
        or approval.get("approval_reference") != approval_reference
        or not approval.get("approval_timestamp_utc")
    ):
        raise ValueError("Valid amendment approval evidence required.")


def build_validated_batch(amendment, approval, source_path, source_file_label,
                          validation_run_id=None, validated_at=None):
    """Return (validated_df, audit_dict) for a PASSED amendment."""
    validation_run_id = (
        validation_run_id or f"VAL-{uuid.uuid4().hex[:12].upper()}"
    )
    validated_at = validated_at or datetime.now(timezone.utc).isoformat()

    source_checksum = hashlib.sha256(
        Path(source_path).read_bytes()
    ).hexdigest()

    # Prepare the Snowflake-compatible curated record.
    validated = amendment.copy()

    validated["detected_rules"] = json.dumps([])
    validated["validation_status"] = "PASS"
    validated["validation_run_id"] = validation_run_id
    validated["validated_at_utc"] = validated_at
    validated["source_file"] = source_file_label
    validated["source_checksum_sha256"] = source_checksum

    row = amendment.iloc[0]

    # Audit record links approval and validation.
    audit = {
        "trade_id": row["trade_id"],
        "trade_version": int(row["trade_version"]),
        "approval_reference": approval["approval_reference"],
        "approval_timestamp_utc": approval["approval_timestamp_utc"],
        "validation_run_id": validation_run_id,
        "validated_at_utc": validated_at,
        "validation_status": "PASS",
        "detected_rules": [],
        "source_checksum_sha256": source_checksum,
        "record_count": len(validated),
        "status": "VALIDATED_PENDING_INGESTION"
    }

    return validated, audit


def main():
    amendment = pd.read_csv(BASE_DIR / "T1001_v2.csv")

    confirmations = pd.read_csv(
        PHASE3_DIR
        / "azure_backup"
        / "raw"
        / "confirmations"
        / "independent_confirmations.csv"
    )

    if len(amendment) != 1:
        raise ValueError("Expected exactly one amended trade.")

    row = amendment.iloc[0]

    if row["trade_id"] != "T-1001" or int(row["trade_version"]) != 2:
        raise ValueError("Unexpected trade or version.")

    errors = revalidate(row, confirmations)

    print("Trade:", row["trade_id"])
    print("Version:", row["trade_version"])
    print("Detected rules:", errors)
    print("Validation status:", "BLOCK" if errors else "PASS")

    if errors:
        raise RuntimeError("Amended trade failed validation.")

    print("AMENDMENT_VALIDATION_PASSED")

    # === AUDITED AMENDMENT BATCH ===

    approval_path = BASE_DIR / "T1001_Approval.json"
    source_path = BASE_DIR / "T1001_v2.csv"

    approval = json.loads(
        approval_path.read_text(encoding="utf-8")
    )

    # Verify documented approval.
    verify_approval(approval)

    # Prevent overwriting existing audit evidence.
    output_dir = BASE_DIR / "validated_output"

    if output_dir.exists():
        raise FileExistsError(
            "Validated output already exists. Review before rerunning."
        )

    validated, audit = build_validated_batch(
        amendment, approval, source_path, "amendments/T1001_v2.csv"
    )

    # Save both outputs without overwriting.
    output_dir.mkdir(parents=True, exist_ok=False)

    validated.to_csv(
        output_dir / "T1001_v2_validated.csv",
        index=False
    )

    with open(
        output_dir / "T1001_v2_audit.json",
        "x",
        encoding="utf-8"
    ) as file:
        json.dump(audit, file, indent=4)

    print("\nAUDITED_AMENDMENT_BATCH_CREATED")
    print("Validation Run ID:", audit["validation_run_id"])
    print("Validation Status: PASS")
    print("Records:", len(validated))
    print("Output:", output_dir)


if __name__ == "__main__":
    main()
