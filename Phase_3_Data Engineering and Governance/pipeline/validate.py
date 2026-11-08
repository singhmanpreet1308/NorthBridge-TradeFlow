import os
from azure.identity import AzureCliCredential, EnvironmentCredential
from datetime import datetime, timezone
import hashlib
import uuid
import io
import pandas as pd
import json

from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core.exceptions import ResourceExistsError


# Azure  & Storage configuration

# Storage configuration
STORAGE_ACCOUNT = "stnorthbridgetradeflow"
FILE_SYSTEM = "northbridge-tradeflow"
VALIDATION_POLICY_VERSION = "1.1"

STORAGE_MODE = os.getenv("STORAGE_MODE", "azure").lower()

if STORAGE_MODE == "local":
    try:
        from pipeline.local_storage import LocalFilesystem
    except ModuleNotFoundError:
        from local_storage import LocalFilesystem

    filesystem = LocalFilesystem()
    print("STORAGE MODE: LOCAL")

elif STORAGE_MODE == "azure":
    # Authentication: Airflow service principal or local Azure CLI
    azure_env_vars = (
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
    )

    if all(os.getenv(name) for name in azure_env_vars):
        credential = EnvironmentCredential()
    else:
        credential = AzureCliCredential()

    service = DataLakeServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net",
        credential=credential
    )

    filesystem = service.get_file_system_client(FILE_SYSTEM)
    print("STORAGE MODE: AZURE")

else:
    raise ValueError(
        f"Unsupported STORAGE_MODE: {STORAGE_MODE}"
    )


def load_csv_from_adls(file_path):
    """Read a CSV directly from the ADLS Gen2 raw layer."""
    file_client = filesystem.get_file_client(file_path)
    file_bytes = file_client.download_file().readall()
    return pd.read_csv(io.BytesIO(file_bytes))


def validate_trade(row):
    """Return a list of validation failures for one trade."""
    errors = []

    def is_missing(value):
        return pd.isna(value) or (
            isinstance(value, str) and not value.strip()
        )

    # DQ-001: Missing trade ID
    if is_missing(row["trade_id"]):
        errors.append("DQ-001")

    # DQ-009: Missing mandatory business fields
    for field in ["counterparty_id", "floating_rate_index"]:
        if is_missing(row[field]):
            errors.append("DQ-009")

    # DQ-004: Notional must be positive
    notional = pd.to_numeric(
        pd.Series([row["notional_amount"]]),
        errors="coerce"
    ).iloc[0]

    if pd.isna(notional) or notional <= 0:
        errors.append("DQ-004")

    # DQ-005: GBP-only demonstration scope
    if row["currency"] != "GBP":
        errors.append("DQ-005")

    # DQ-006: Maturity must follow effective date
    effective = pd.to_datetime(row["effective_date"], errors="coerce")
    maturity = pd.to_datetime(row["maturity_date"], errors="coerce")

    if pd.isna(effective) or pd.isna(maturity) or maturity <= effective:
        errors.append("DQ-006")

    # DQ-007: Demonstration-only fixed-rate range
    rate = pd.to_numeric(
        pd.Series([row["fixed_rate"]]),
        errors="coerce"
    ).iloc[0]

    if pd.isna(rate) or not (0 < rate <= 0.15):
        errors.append("DQ-007")

    # DQ-008: Valid fixed-leg direction
    if row["pay_receive_fixed"] not in ["PAY", "RECEIVE"]:
        errors.append("DQ-008")

    return list(dict.fromkeys(errors))


def reconcile_confirmation(row, confirmations):
    """Check trade notional against independent confirmation."""
    errors = []

    trade_id = row["trade_id"]

    if pd.isna(trade_id):
        return errors  # DQ-001 handles missing trade IDs.

    matching = confirmations[
        confirmations["trade_id"] == trade_id
    ]

    if len(matching) == 0:
        errors.append("RECON_MISSING_CONFIRMATION")
        return errors

    if len(matching) > 1:
        errors.append("RECON_DUPLICATE_CONFIRMATION")
        return errors

    confirmation = matching.iloc[0]

    trade_notional = pd.to_numeric(
        row["notional_amount"], errors="coerce"
    )

    confirmed_notional = pd.to_numeric(
        confirmation["notional_amount"], errors="coerce"
    )

    if (
        pd.notna(trade_notional)
        and pd.notna(confirmed_notional)
        and abs(trade_notional - confirmed_notional) > 0.01
    ):
        errors.append("DEMO_NOTIONAL_MISMATCH")

    return errors


def verify_error_manifest(seeded_errors, confirmations, manifest):
    results = []

    for _, expected in manifest.iterrows():
        fixture_id = expected["fixture_trade_id"]
        expected_rule = expected["expected_rule"]
        expected_outcome = expected["expected_outcome"]

        source_ref = f"OMS-{str(fixture_id).split('-')[-1]}"

        matching = seeded_errors[
            seeded_errors["source_trade_ref"] == source_ref
        ]

        if len(matching) != 1:
            results.append({
                "trade_id": fixture_id,
                "expected_rule": expected_rule,
                "actual_outcome": "NOT_EVALUATED",
                "test_result": "FAIL"
            })
            continue

        row = matching.iloc[0]
        detected_rules = validate_trade(row)

        if "DQ-004" not in detected_rules:
            detected_rules += reconcile_confirmation(
                row, confirmations
            )

        actual_outcome = "BLOCK" if detected_rules else "PASS"

        test_passed = (
            expected_rule in detected_rules
            and actual_outcome == expected_outcome
        )

        results.append({
            "trade_id": fixture_id,
            "expected_rule": expected_rule,
            "actual_outcome": actual_outcome,
            "test_result": "PASS" if test_passed else "FAIL"
        })

    return pd.DataFrame(results)

def get_adls_file_checksum(file_path):
    """Calculate SHA-256 checksum of the original ADLS file."""
    file_client = filesystem.get_file_client(file_path)
    file_bytes = file_client.download_file().readall()

    return hashlib.sha256(file_bytes).hexdigest()


def check_adls_file_exists(file_path):
    """Check whether a file already exists in ADLS Gen2."""
    file_client = filesystem.get_file_client(file_path)

    return file_client.exists()


def upload_adls_file(file_path, content):
    """Upload a file to ADLS Gen2 without overwriting it."""

    file_client = filesystem.get_file_client(file_path)

    if isinstance(content, str):
        content = content.encode("utf-8")

    try:
        # Conditional creation prevents replacing an existing file.
        file_client.create_file(
            if_none_match="*"
        )

        file_client.append_data(
            data=content,
            offset=0,
            length=len(content)
        )

        file_client.flush_data(len(content))

        print(f"UPLOADED: {file_path}")

    except (ResourceExistsError, FileExistsError):
        raise RuntimeError(
            f"Upload blocked: file already exists: {file_path}"
        )

    
def test_adls_upload():
    """Test Azure upload and no-overwrite protection."""

    test_path = "curated/test/upload_safety_check.txt"
    test_content = b"NorthBridge TradeFlow upload test"

    if check_adls_file_exists(test_path):
        print("Test file already exists. Skipping upload test.")
        return

    print("\n=== AZURE UPLOAD SAFETY TEST ===")

    upload_adls_file(test_path, test_content)

    assert check_adls_file_exists(test_path)

    print("Initial upload: PASS")

    try:
        upload_adls_file(test_path, test_content)
    except RuntimeError:
        print("Overwrite protection: PASS")
    else:
        raise AssertionError(
            "Overwrite protection failed!"
        )

    
def upload_and_verify(file_path, content):
    """Upload a new ADLS file and verify its exact contents."""

    if isinstance(content, str):
        content = content.encode("utf-8")

    # Refuse to replace an existing output.
    if check_adls_file_exists(file_path):
        raise RuntimeError(
            f"Output already exists; manual review required: {file_path}"
        )

    upload_adls_file(file_path, content)

    # Read back the uploaded bytes.
    actual = (
        filesystem
        .get_file_client(file_path)
        .download_file()
        .readall()
    )

    if hashlib.sha256(actual).digest() != hashlib.sha256(content).digest():
        raise RuntimeError(
            f"Upload integrity verification failed: {file_path}"
        )

    print(f"VERIFIED: {file_path} ({len(actual)} bytes)")


def verify_completed_batch(batch_id, completion_path, output_paths):
    """Verify a completed batch before skipping processing."""

    marker_bytes = (
        filesystem
        .get_file_client(completion_path)
        .download_file()
        .readall()
    )

    marker = json.loads(marker_bytes)

    print("\n=== COMPLETION MARKER FIELDS ===")
    print(sorted(marker.keys()))

    if marker.get("batch_id") != batch_id:
        raise RuntimeError("Completion marker batch ID mismatch.")

    if marker.get("status") != "COMPLETED":
        raise RuntimeError("Batch is not marked COMPLETED.")

    expected_outputs = {
        "curated": output_paths["Curated"],
        "quarantine": output_paths["Quarantine"],
        "audit": output_paths["Audit"]
    }

    for name, expected_path in expected_outputs.items():
        actual_path = marker.get("outputs", {}).get(name)

        if actual_path != expected_path:
            raise RuntimeError(
                f"Completion marker path mismatch: {name}"
            )

        if not check_adls_file_exists(expected_path):
            raise RuntimeError(
                f"Completed batch is missing output: {expected_path}"
            )

    print("Completion marker: VALID")
    print("All three output files: PRESENT")

    return True


def verify_adls_content(file_path, expected_content):
    """Verify stored ADLS content matches expected output bytes."""

    if isinstance(expected_content, str):
        expected_content = expected_content.encode("utf-8")

    actual_content = (
        filesystem
        .get_file_client(file_path)
        .download_file()
        .readall()
    )

    expected_hash = hashlib.sha256(
        expected_content
    ).hexdigest()

    actual_hash = hashlib.sha256(
        actual_content
    ).hexdigest()

    if actual_hash != expected_hash:
        raise RuntimeError(
            f"Content integrity failure: {file_path}"
        )

    print(f"INTEGRITY PASS: {file_path}")
    return True


def inspect_persisted_outputs(output_paths):
    """Inspect actual stored output files without modifying Azure."""

    print("\n=== PERSISTED OUTPUT INTEGRITY ===")

    for name, file_path in output_paths.items():
        stored_bytes = (
            filesystem
            .get_file_client(file_path)
            .download_file()
            .readall()
        )

        stored_checksum = hashlib.sha256(
            stored_bytes
        ).hexdigest()

        print(f"\n{name}:")
        print(f"  Path: {file_path}")
        print(f"  Size: {len(stored_bytes)} bytes")
        print(f"  SHA-256: {stored_checksum}")
    
    print("\nStored output inspection: COMPLETED")


def build_output_checksum_manifest(batch_id, output_paths):
    """Build a checksum manifest from the stored Azure outputs."""

    checksums = {}

    for name, path in output_paths.items():
        content = (
            filesystem
            .get_file_client(path)
            .download_file()
            .readall()
        )

        checksums[name.lower()] = {
            "path": path,
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest()
        }

    return {
        "batch_id": batch_id,
        "manifest_type": "POST_UPLOAD_BASELINE",
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "outputs": checksums
    }

def verify_output_checksums(batch_id, output_paths):
    """Verify stored outputs against the saved checksum manifest."""

    manifest_path = (
        f"curated/audit/{batch_id}/output_checksums.json"
    )

    if not check_adls_file_exists(manifest_path):
        raise RuntimeError(
            f"Checksum manifest missing: {manifest_path}"
        )

    manifest_bytes = (
        filesystem
        .get_file_client(manifest_path)
        .download_file()
        .readall()
    )

    manifest = json.loads(manifest_bytes)

    if manifest.get("batch_id") != batch_id:
        raise RuntimeError("Checksum manifest batch ID mismatch.")

    print("\n=== AUTOMATIC OUTPUT CHECKSUM VERIFICATION ===")

    for name, file_path in output_paths.items():
        entry = manifest.get("outputs", {}).get(name.lower())

        if not isinstance(entry, dict):
            raise RuntimeError(
                f"Missing checksum entry for {name}"
            )

        if entry.get("path") != file_path:
            raise RuntimeError(
                f"Output path mismatch for {name}"
            )

        stored_bytes = (
            filesystem
            .get_file_client(file_path)
            .download_file()
            .readall()
        )

        actual_size = len(stored_bytes)
        actual_hash = hashlib.sha256(stored_bytes).hexdigest()

        if actual_size != entry.get("size_bytes"):
            raise RuntimeError(
                f"File size mismatch: {file_path}"
            )

        if actual_hash != entry.get("sha256"):
            raise RuntimeError(
                f"SHA-256 mismatch: {file_path}"
            )

        print(f"{name}: INTEGRITY PASS")

    print("All stored output checksums verified.")
    return True


def main():
    # Keep baseline trades and seeded test fixtures separate.
    trades = load_csv_from_adls(
        "raw/trades/sample_trades.csv"
    )

    confirmations = load_csv_from_adls(
        "raw/confirmations/independent_confirmations.csv"
    )

    seeded_errors = load_csv_from_adls(
        "raw/reference/seeded_errors.csv"
    )

    manifest = load_csv_from_adls(
        "raw/reference/seeded_error_manifest.csv"
    )

    print("\n=== VALIDATION INPUT SUMMARY ===")
    print(f"Baseline trades: {len(trades)}")
    print(f"Independent confirmations: {len(confirmations)}")
    print(f"Seeded test fixtures: {len(seeded_errors)}")
    print(f"Expected defect scenarios: {len(manifest)}")

    print("\n=== SCHEMA CHECK ===")

    required_trade_columns = [
        "trade_id",
        "trade_version",
        "counterparty_id",
        "currency",
        "notional_amount",
        "fixed_rate",
        "floating_rate_index",
        "pay_receive_fixed",
        "effective_date",
        "maturity_date"
    ]

    for dataset_name, df in [
        ("Baseline trades", trades),
        ("Seeded errors", seeded_errors)
    ]:
        missing_columns = [
            col for col in required_trade_columns
            if col not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"{dataset_name}: missing columns {missing_columns}"
            )

        print(f"{dataset_name}: schema columns present")

   
    print("\n=== SEEDED TRADE VALIDATION ===")

    for _, row in seeded_errors.iterrows():

        # Step 1: Validate individual trade fields
        detected_rules = validate_trade(row)

        # Step 2: Reconcile against independent confirmation
        # Reconcile only when the notional passes basic validation.
        # Invalid negative/zero notionals are already blocked by DQ-004.
        if "DQ-004" not in detected_rules:
            reconciliation_rules = reconcile_confirmation(row, confirmations)
        else:
            reconciliation_rules = []

        # Step 3: Combine validation failures
        detected_rules = list(
            dict.fromkeys(
                detected_rules + reconciliation_rules
            )
        )

        # Step 4: Display results
        source_ref = row["source_trade_ref"]

        print(
            f"{source_ref} | "
            f"Detected rules: {detected_rules or ['PASS']}"
        )
    
    print("\n=== ERROR MANIFEST VERIFICATION ===")

    verification = verify_error_manifest(
        seeded_errors,
        confirmations,
        manifest
    )

    print(
        verification[
            [
                "trade_id",
                "expected_rule",
                "actual_outcome",
                "test_result"
            ]
        ].to_string(index=False)
    )

    passed = (verification["test_result"] == "PASS").sum()
    total = len(verification)

    print(f"\nManifest verification: {passed}/{total} passed")

    if passed != total:
        raise AssertionError(
            f"Manifest verification failed: {total - passed} scenarios"
        )

    
    print("\n=== BASELINE TRADE VALIDATION ===")

    baseline_results = []

    for _, row in trades.iterrows():
        detected_rules = validate_trade(row)

        if "DQ-004" not in detected_rules:
            detected_rules += reconcile_confirmation(
                row, confirmations
            )

        detected_rules = list(dict.fromkeys(detected_rules))

        baseline_results.append({
            "trade_id": row["trade_id"],
            "trade_version": row["trade_version"],
            "detected_rules": detected_rules,
            "validation_status": (
                "BLOCK" if detected_rules else "PASS"
            )
        })

    baseline_df = pd.DataFrame(baseline_results)

    # Verify baseline validation results.
    baseline_pass = sum(
        result["validation_status"] == "PASS"
        for result in baseline_results
    )

    baseline_block = sum(
        result["validation_status"] == "BLOCK"
        for result in baseline_results
    )

    print("\n=== BASELINE VALIDATION CONTROL CHECK ===")
    print(f"PASS: {baseline_pass}")
    print(f"BLOCK: {baseline_block}")

    if baseline_pass != 49 or baseline_block != 1:
        raise RuntimeError(
            "Baseline validation counts changed. "
            "Review reconciliation rules before publishing."
        )

    print("Baseline validation control: PASSED")


    print("\nValidation status summary:")
    print(
        baseline_df["validation_status"]
        .value_counts()
        .to_string()
    )

    print("\nBlocked baseline trades:")
    print(
        baseline_df[
            baseline_df["validation_status"] == "BLOCK"
        ].to_string(index=False)
    )

    print("\n=== CURATED AND QUARANTINE PREVIEW ===")

    # Preserve the complete original trade records.
    # Match validation results using the trade/version composite key.
    trade_results = trades.merge(
        baseline_df[
            [
                "trade_id",
                "trade_version",
                "detected_rules",
                "validation_status"
            ]
        ],
        on=["trade_id", "trade_version"],
        how="left",
        validate="one_to_one"
    )

    if trade_results["validation_status"].isna().any():
        raise ValueError("Some trades have no validation result.")

    # Valid trades eligible for downstream processing.
    curated_df = trade_results[
        trade_results["validation_status"] == "PASS"
    ].copy()

    # Blocked trades requiring investigation.
    quarantine_df = trade_results[
        trade_results["validation_status"] == "BLOCK"
    ].copy()

    print(f"Curated records: {len(curated_df)}")
    print(f"Quarantine records: {len(quarantine_df)}")

    # Ensure no trade is lost or counted twice.
    assert len(curated_df) + len(quarantine_df) == len(trades)

    print("\nQuarantine preview:")
    print(
        quarantine_df[
            [
                "trade_id",
                "trade_version",
                "notional_amount",
                "detected_rules",
                "validation_status"
            ]
        ].to_string(index=False)
    )


    print("\n=== VALIDATION AUDIT METADATA ===")

    validation_run_id = f"VAL-{uuid.uuid4().hex[:12].upper()}"
    validated_at = datetime.now(timezone.utc).isoformat()

    # Attach lineage metadata to both output datasets.
    for df in [curated_df, quarantine_df]:
        df["validation_run_id"] = validation_run_id
        df["validated_at_utc"] = validated_at
        df["source_file"] = "raw/trades/sample_trades.csv"

    print(f"Validation Run ID: {validation_run_id}")
    print(f"Validated At (UTC): {validated_at}")
    print(f"Curated Records: {len(curated_df)}")
    print(f"Quarantine Records: {len(quarantine_df)}")

    print("\nQuarantine audit preview:")
    print(
        quarantine_df[
            [
                "trade_id",
                "trade_version",
                "validation_status",
                "detected_rules",
                "validation_run_id",
                "validated_at_utc",
                "source_file"
            ]
        ].to_string(index=False)
    )


    print("\n=== SOURCE CHECKSUM VERIFICATION ===")

    source_path = "raw/trades/sample_trades.csv"

    source_checksum = get_adls_file_checksum(source_path)

    # Attach checksum to both output datasets.
    for df in [curated_df, quarantine_df]:
        df["source_checksum_sha256"] = source_checksum

    print(f"Source file: {source_path}")
    print(f"SHA-256: {source_checksum}")
    print(f"Checksum length: {len(source_checksum)}")

    assert len(source_checksum) == 64

    print("Source checksum verification: PASS")


    print("\n=== AZURE OUTPUT PATH PREVIEW ===")

    # Stable batch identifier derived from source content.
    
    # Identify the exact inputs and validation policy used.
    confirmation_checksum = get_adls_file_checksum(
        "raw/confirmations/independent_confirmations.csv"
    )

    batch_identity = (
        f"{source_checksum}|"
        f"{confirmation_checksum}|"
        f"{VALIDATION_POLICY_VERSION}"
    )

    batch_hash = hashlib.sha256(
        batch_identity.encode("utf-8")
    ).hexdigest()

    batch_id = f"BATCH-{batch_hash[:16].upper()}"

    print(f"Validation policy: {VALIDATION_POLICY_VERSION}")
    print(f"Confirmation checksum: {confirmation_checksum}")


    curated_path = (
        f"curated/trades/{batch_id}/validated_trades.csv"
    )

    quarantine_path = (
        f"quarantine/trades/{batch_id}/blocked_trades.csv"
    )

    audit_path = (
        f"curated/audit/{batch_id}/validation_summary.json"
    )

    print(f"Batch ID: {batch_id}")
    print(f"Curated path: {curated_path}")
    print(f"Quarantine path: {quarantine_path}")
    print(f"Audit path: {audit_path}")

    print("\nOutput path preparation: PASS")


    print("\n=== EXISTING BATCH CHECK ===")

    output_paths = {
        "Curated": curated_path,
        "Quarantine": quarantine_path,
        "Audit": audit_path
    }

    existing_outputs = {
        name: check_adls_file_exists(path)
        for name, path in output_paths.items()
    }

    for name, exists in existing_outputs.items():
        print(
            f"{name}: {'EXISTS' if exists else 'NOT FOUND'}"
        )

    if all(existing_outputs.values()):
        print("\nBatch outputs already exist. Do not overwrite.")
    elif any(existing_outputs.values()):
        print(
            "\nWARNING: Partial batch outputs detected. "
            "Manual investigation required before writing."
        )
    else:
        print("\nNo existing batch outputs. Ready for initial write.")

    
    print("\n=== AZURE OUTPUT PAYLOAD PREPARATION ===")

    # Convert rule lists to JSON strings for CSV compatibility.
    curated_export = curated_df.copy()
    quarantine_export = quarantine_df.copy()


    print("\n=== SNOWFLAKE CURATED TABLE COLUMNS ===")
    print(curated_export.columns.tolist())
    print("\n=== CURATED COLUMN DATA TYPES ===")
    print(curated_export.dtypes.to_string())


    for df in [curated_export, quarantine_export]:
        df["detected_rules"] = df["detected_rules"].apply(
            json.dumps
        )

    curated_csv = curated_export.to_csv(index=False)
    quarantine_csv = quarantine_export.to_csv(index=False)

    validation_summary = {
        "batch_id": batch_id,
        "validation_run_id": validation_run_id,
        "validated_at_utc": validated_at,
        "validation_policy_version": VALIDATION_POLICY_VERSION,
        "source_file": source_path,
        "source_checksum_sha256": source_checksum,
        "confirmation_file": (
            "raw/confirmations/independent_confirmations.csv"
        ),
        "confirmation_checksum_sha256": confirmation_checksum,
        "total_trades": len(trades),
        "curated_records": len(curated_df),
        "quarantine_records": len(quarantine_df),
        "manifest_tests_passed": int(passed),
        "manifest_tests_total": int(total),
        "status": "VALIDATED"
    }

    audit_json = json.dumps(
        validation_summary,
        indent=2
    )

    print(f"Curated CSV bytes: {len(curated_csv.encode('utf-8'))}")
    print(f"Quarantine CSV bytes: {len(quarantine_csv.encode('utf-8'))}")
    print(f"Audit JSON bytes: {len(audit_json.encode('utf-8'))}")

    print("\nAudit summary preview:")
    print(audit_json)

    test_adls_upload()


    print("\n=== CONTROLLED AZURE BATCH UPLOAD ===")

    completion_path = (
        f"curated/audit/{batch_id}/_SUCCESS.json"
    )
    if check_adls_file_exists(completion_path):

        print(f"\nExisting batch detected: {batch_id}")

        verify_completed_batch(
            batch_id,
            completion_path,
            output_paths
        )
        verify_output_checksums(batch_id,output_paths)

        inspect_persisted_outputs(output_paths)

        print("\n=== OUTPUT CHECKSUM MANIFEST PREVIEW ===")

        checksum_manifest = build_output_checksum_manifest(
            batch_id,
            output_paths
        )

        print(json.dumps(checksum_manifest, indent=2))

        checksum_manifest_path = (
            f"curated/audit/{batch_id}/output_checksums.json"
        )

        if check_adls_file_exists(checksum_manifest_path):
            print("\nChecksum manifest already exists. Skipping creation.")
        else:
            checksum_manifest_json = json.dumps(
                checksum_manifest,
                indent=2
            )

            upload_and_verify(
                checksum_manifest_path,
                checksum_manifest_json
            )

            print("\nChecksum manifest saved successfully.")

    if check_adls_file_exists(completion_path):

        print(f"\nExisting batch detected: {batch_id}")

        verify_completed_batch(
            batch_id,
            completion_path,
            output_paths
        )

        inspect_persisted_outputs(output_paths)

        print("\n=== OUTPUT CHECKSUM MANIFEST PREVIEW ===")

        checksum_manifest = build_output_checksum_manifest(
            batch_id,
            output_paths
        )

        print(json.dumps(checksum_manifest, indent=2))

        checksum_manifest_path = (
            f"curated/audit/{batch_id}/output_checksums.json"
        )

        if check_adls_file_exists(checksum_manifest_path):
            print("\nChecksum manifest already exists. Skipping creation.")
        else:
            checksum_manifest_json = json.dumps(
                checksum_manifest,
                indent=2
            )

            upload_and_verify(
                checksum_manifest_path,
                checksum_manifest_json
            )

            print("\nChecksum manifest saved successfully.")

        # NEW: Verify stored files against the saved checksum manifest.
        verify_output_checksums(
            batch_id,
            output_paths
        )

        print("\nExisting outputs will not be overwritten.")
        print("Batch status: SKIPPED")

        return

    # Never reprocess a completed batch.
    if check_adls_file_exists(completion_path):
        print(f"\nExisting batch detected: {batch_id}")
        verify_completed_batch(batch_id,completion_path,output_paths)


        # Verify persisted outputs against the newly generated payloads.
        # verify_adls_content(curated_path, curated_csv)
        # verify_adls_content(quarantine_path, quarantine_csv)
        # verify_adls_content(audit_path, audit_json)


        print("Existing outputs will not be overwritten.")
        print("Batch status: SKIPPED")

        return 

    # Do not proceed if any partial output exists.
    for path in [curated_path, quarantine_path, audit_path, f"curated/audit/{batch_id}/output_checksums.json"]:
        if check_adls_file_exists(path):
            raise RuntimeError(
                f"Partial batch detected. Investigate: {path}"
            )

    # Basic consistency checks before uploading.
    assert len(curated_df) + len(quarantine_df) == len(trades)
    assert passed == total == 10

    upload_and_verify(curated_path, curated_csv)
    upload_and_verify(quarantine_path, quarantine_csv)
    upload_and_verify(audit_path, audit_json)

    # Create checksum baseline for newly uploaded outputs.
    checksum_manifest_path = (
        f"curated/audit/{batch_id}/output_checksums.json"
    )

    if check_adls_file_exists(checksum_manifest_path):
        raise RuntimeError(
            f"Unexpected checksum manifest already exists: "
            f"{checksum_manifest_path}"
        )

    checksum_manifest = build_output_checksum_manifest(
        batch_id,
        output_paths
    )

    checksum_manifest_json = json.dumps(
        checksum_manifest,
        indent=2
    )

    upload_and_verify(
        checksum_manifest_path,
        checksum_manifest_json
    )

    # Verify all persisted outputs against the saved baseline.
    verify_output_checksums(
        batch_id,
        output_paths
    )

    print("\nNew batch checksum verification: PASSED")


    # Completion marker is written last.
    completion_marker = {
        "batch_id": batch_id,
        "status": "COMPLETED",
        "completed_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "validation_run_id": validation_run_id,
        "outputs": {
            "curated": curated_path,
            "quarantine": quarantine_path,
            "audit": audit_path
        }
    }

    upload_and_verify(
        completion_path,
        json.dumps(completion_marker, indent=2)
    )

    print("\nBatch upload completed successfully.")
    print(f"Completion marker: {completion_path}")


    
    print("\nValidation checks completed.")




if __name__ == "__main__":
    main()
