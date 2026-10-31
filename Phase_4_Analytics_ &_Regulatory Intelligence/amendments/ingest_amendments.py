
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from getpass import getpass
from decimal import Decimal

import snowflake.connector
from cryptography.hazmat.primitives import serialization

BASE_DIR = Path(__file__).resolve().parent
TABLE = "NORTHBRIDGE_TRADEFLOW.CURATED.TRADES_VALIDATED"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect_snowflake():
    key_path = (
        Path.home() / ".snowflake" / "northbridge_rsa_key.pem"
    )

    passphrase = getpass("RSA private key passphrase: ")

    with open(key_path, "rb") as f:
        key = serialization.load_pem_private_key(
            f.read(),
            password=passphrase.encode("utf-8")
        )

    key_bytes = key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user="NORTHBRIDGE_INGEST_USER",
        private_key=key_bytes,
        role="NORTHBRIDGE_INGEST_ROLE",
        warehouse="NORTHBRIDGE_WH",
        database="NORTHBRIDGE_TRADEFLOW",
        schema="CURATED"
    )


def verify_batch(csv_path, audit_path, approval_path,
                 source_path):

    audit = read_json(audit_path)
    approval = read_json(approval_path)

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)

    if not columns or len(set(columns)) != len(columns):
        raise ValueError("Invalid or duplicate CSV columns.")

    if len(rows) != 1 or audit.get("record_count") != 1:
        raise ValueError(
            "This amendment batch must contain exactly one row."
        )

    row = rows[0]

    trade_id = row["trade_id"]
    version = int(row["trade_version"])

    if (
        trade_id != approval.get("trade_id")
        or trade_id != audit.get("trade_id")
        or version != int(approval["amended_version"])
        or version != int(audit["trade_version"])
    ):
        raise ValueError("Trade/version identity mismatch.")

    if version <= int(approval["original_version"]):
        raise ValueError("Amendment version is not newer.")

    if (
        approval.get("approval_status") != "APPROVED"
        or not approval.get("approval_timestamp_utc")
        or not approval.get("approved_by")
        or not approval.get("approval_reference")
        or approval["approval_reference"]
        != audit.get("approval_reference")
        or approval["approval_timestamp_utc"]
        != audit.get("approval_timestamp_utc")
    ):
        raise ValueError("Approval verification failed.")

    if (
        row["validation_status"] != "PASS"
        or audit.get("validation_status") != "PASS"
        or audit.get("status") != "VALIDATED_PENDING_INGESTION"
        or json.loads(row["detected_rules"]) != []
        or audit.get("detected_rules") != []
        or row["validation_run_id"]
        != audit.get("validation_run_id")
        or row["validated_at_utc"]
        != audit.get("validated_at_utc")
    ):
        raise ValueError("Validation evidence mismatch.")

    if (
        Decimal(row["notional_amount"])
        != Decimal(str(approval["corrected_notional_gbp"]))
    ):
        raise ValueError("Approved notional mismatch.")

    if (
        sha256(source_path)
        != audit["source_checksum_sha256"]
        or row["source_checksum_sha256"]
        != audit["source_checksum_sha256"]
    ):
        raise ValueError("Source checksum mismatch.")

    # Verify that the validated CSV still contains
    # the same source trade fields.
    with source_path.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        source_rows = list(csv.DictReader(f))

    if len(source_rows) != 1:
        raise ValueError("Invalid source amendment.")

    for field, value in source_rows[0].items():
        if row.get(field, "") != value:
            raise ValueError(
                f"Source field changed after validation: {field}"
            )

    print("APPROVAL_VERIFIED")
    print("VALIDATION_VERIFIED")
    print("SOURCE_CHECKSUM_VERIFIED")
    print("TRADE:", trade_id, "VERSION:", version)

    return columns, row


def ingest(columns, row, commit=False):
    connection = connect_snowflake()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT COLUMN_NAME
                FROM NORTHBRIDGE_TRADEFLOW
                    .INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'CURATED'
                  AND TABLE_NAME = 'TRADES_VALIDATED'
                ORDER BY ORDINAL_POSITION
            """)

            expected_columns = [
                r[0] for r in cursor.fetchall()
            ]

            actual_columns = [c.upper() for c in columns]

            if (
                len(actual_columns) != 26
                or set(actual_columns) != set(expected_columns)
            ):
                raise ValueError(
                    "CSV and Snowflake schemas do not match."
                )

            cursor.execute(
                f"""SELECT COUNT(*) FROM {TABLE}
                    WHERE TRADE_ID = %s
                      AND TRADE_VERSION = %s""",
                (row["trade_id"], int(row["trade_version"]))
            )

            if cursor.fetchone()[0] != 0:
                raise ValueError(
                    "Trade version already exists in Snowflake."
                )

            cursor.execute(
                f"""SELECT COUNT(*) FROM {TABLE}
                    WHERE VALIDATION_RUN_ID = %s""",
                (row["validation_run_id"],)
            )

            if cursor.fetchone()[0] != 0:
                raise ValueError(
                    "Validation run ID already exists."
                )

            print("SNOWFLAKE_PRECHECK_PASSED")

            if not commit:
                print("DRY_RUN_PASSED — no records inserted")
                return

            values = [row[c] if row[c] != "" else None
                      for c in columns]

            placeholders = ", ".join(["%s"] * len(columns))
            column_names = ", ".join(actual_columns)

            cursor.execute("BEGIN")

            try:
                cursor.execute(
                    f"""INSERT INTO {TABLE} ({column_names})
                        VALUES ({placeholders})""",
                    tuple(values)
                )

                cursor.execute(
                    f"""SELECT COUNT(*) FROM {TABLE}
                        WHERE TRADE_ID = %s
                          AND TRADE_VERSION = %s""",
                    (row["trade_id"],
                     int(row["trade_version"]))
                )

                if cursor.fetchone()[0] != 1:
                    raise RuntimeError(
                        "Post-insertion verification failed."
                    )

                cursor.execute("COMMIT")
                print("AMENDMENT_INGESTION_SUCCESS")

            except Exception:
                cursor.execute("ROLLBACK")
                raise

    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true")
    parser.add_argument(
        "--csv",
        type=Path,
        default=BASE_DIR / "validated_output"
        / "T1001_v2_validated.csv"
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=BASE_DIR / "validated_output"
        / "T1001_v2_audit.json"
    )
    parser.add_argument(
        "--approval",
        type=Path,
        default=BASE_DIR / "T1001_Approval.json"
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=BASE_DIR / "T1001_v2.csv"
    )

    args = parser.parse_args()

    columns, row = verify_batch(
        args.csv, args.audit, args.approval, args.source
    )

    ingest(columns, row, commit=args.commit)


if __name__ == "__main__":
    main()
