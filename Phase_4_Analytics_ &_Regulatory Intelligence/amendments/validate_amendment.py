
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
    / "Phase_3_Data_Engineering"
)

sys.path.insert(0, str(PHASE3_DIR))

from pipeline.validate import (
    validate_trade,
    reconcile_confirmation
)

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

errors = validate_trade(row)

if "DQ-004" not in errors:
    errors += reconcile_confirmation(row, confirmations)

errors = list(dict.fromkeys(errors))

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
if (
    approval.get("approval_status") != "APPROVED"
    or approval.get("trade_id") != "T-1001"
    or int(approval.get("amended_version", -1)) != 2
    or approval.get("approval_reference") != "NB-T1001-APP-001"
    or not approval.get("approval_timestamp_utc")
):
    raise ValueError("Valid amendment approval evidence required.")

# Prevent overwriting existing audit evidence.
output_dir = BASE_DIR / "validated_output"

if output_dir.exists():
    raise FileExistsError(
        "Validated output already exists. Review before rerunning."
    )

# Generate audit identifiers and metadata.
validation_run_id = f"VAL-{uuid.uuid4().hex[:12].upper()}"
validated_at = datetime.now(timezone.utc).isoformat()

source_checksum = hashlib.sha256(
    source_path.read_bytes()
).hexdigest()

# Prepare the Snowflake-compatible curated record.
validated = amendment.copy()

validated["detected_rules"] = json.dumps([])
validated["validation_status"] = "PASS"
validated["validation_run_id"] = validation_run_id
validated["validated_at_utc"] = validated_at
validated["source_file"] = "amendments/T1001_v2.csv"
validated["source_checksum_sha256"] = source_checksum

# Audit record links approval and validation.
audit = {
    "trade_id": "T-1001",
    "trade_version": 2,
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
print("Validation Run ID:", validation_run_id)
print("Validation Status: PASS")
print("Records:", len(validated))
print("Output:", output_dir)

