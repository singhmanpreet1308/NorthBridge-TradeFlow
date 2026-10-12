import json
import sys
import os
from pathlib import Path

from getpass import getpass

import snowflake.connector
from cryptography.hazmat.primitives import serialization

from audit.audit_logger import log_ingestion_event



# Import the existing Azure ADLS Gen2 reader.
PIPELINE_DIR = Path(__file__).resolve().parents[1] / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from validate import load_csv_from_adls

BATCH_ID = "BATCH-60FD5666D0A1FBAD"

VALIDATION_RUN_ID = "VAL-E6532CDFF204"


CURATED_PATH = (
    f"curated/trades/{BATCH_ID}/validated_trades.csv"
)


def connect_to_snowflake():
    """Connect to Snowflake using the encrypted RSA private key."""

    private_key_path = (
        Path.home() / ".snowflake" / "northbridge_rsa_key.pem"
    )

    passphrase = getpass("Enter RSA private key passphrase: ")

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=passphrase.encode("utf-8"),
        )

    private_key_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(
        account="LYUDTKG-OC94773",
        user="NORTHBRIDGE_INGEST_USER",
        private_key=private_key_der,
        role="NORTHBRIDGE_INGEST_ROLE",
        warehouse="NORTHBRIDGE_WH",
        database="NORTHBRIDGE_TRADEFLOW",
        schema="CURATED",
    )


def ingest_validated_trades(connection, df, validation_run_id):
    """Insert validated trades in one transaction."""

    table_name = "NORTHBRIDGE_TRADEFLOW.CURATED.TRADES_VALIDATED"

    columns = [column.upper() for column in df.columns]

    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join(columns)

    insert_sql = f"""
        INSERT INTO {table_name} ({column_names})
        VALUES ({placeholders})
    """

    # Convert pandas missing values and timestamps for Snowflake.
    import pandas as pd

    date_columns = {
        "capture_timestamp",
        "trade_date",
        "effective_date",
        "maturity_date",
        "record_timestamp",
        "validated_at_utc",
    }


    prepared_df = df.copy()

    for column in date_columns:
        if column in prepared_df.columns:
            parsed_dates = pd.to_datetime(
                prepared_df[column],
                errors="raise",
                utc=True,
            )

            prepared_df[column] = parsed_dates.dt.strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )

    # Convert missing values to Python None.
    # This applies to the entire DataFrame, not one column.
    prepared_df = prepared_df.astype(object).where(
        pd.notna(prepared_df), None
    )

    rows = [
        tuple(row)
        for row in prepared_df.itertuples(index=False, name=None)
    ]

    try:
        connection.autocommit(False)

        with connection.cursor() as cursor:
            # Recheck inside the ingestion transaction.
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE VALIDATION_RUN_ID = %s
                """,
                (validation_run_id,),
            )

            existing_count = cursor.fetchone()[0]

           
            if existing_count == len(df):
                print(
                    f"BATCH_ALREADY_EXISTS: "
                    f"{existing_count} records"
                )
                connection.rollback()
                return

            elif existing_count != 0:
                raise ValueError(
                    f"PARTIAL_OR_UNEXPECTED_BATCH: "
                    f"expected {len(df)} records, "
                    f"found {existing_count}"
                )


            cursor.executemany(insert_sql, rows)

            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE VALIDATION_RUN_ID = %s
                """,
                (validation_run_id,),
            )

            loaded_count = cursor.fetchone()[0]

            if loaded_count != len(df):
                raise ValueError(
                    f"Count mismatch: expected {len(df)}, "
                    f"found {loaded_count}"
                )

        connection.commit()

        print(f"SNOWFLAKE_INGESTION_SUCCESS: {loaded_count} trades")

    except Exception:
        connection.rollback()
        print("SNOWFLAKE_INGESTION_ROLLED_BACK")
        raise

    finally:
        connection.autocommit(True)



def verify_batch_completion():
    """Verify the batch completion marker in Azure or local storage."""

    storage_mode = os.getenv("STORAGE_MODE", "azure").lower()

    marker_path = f"curated/audit/{BATCH_ID}/_SUCCESS.json"

    if storage_mode == "local":
        from local_storage import read_bytes
        marker_data = read_bytes(marker_path)

    elif storage_mode == "azure":
        from azure.identity import DefaultAzureCredential
        from azure.storage.filedatalake import DataLakeServiceClient

        account_url = (
            "https://stnorthbridgetradeflow.dfs.core.windows.net"
        )

        credential = DefaultAzureCredential()

        service_client = DataLakeServiceClient(
            account_url=account_url,
            credential=credential,
        )

        filesystem = service_client.get_file_system_client(
            "northbridge-tradeflow"
        )

        marker_client = filesystem.get_file_client(marker_path)
        marker_data = marker_client.download_file().readall()

    else:
        raise ValueError(
            f"Unsupported STORAGE_MODE: {storage_mode}"
        )

    marker = json.loads(marker_data)

    print("\n=== COMPLETION MARKER METADATA ===")
    print(json.dumps(marker, indent=2))

    print("BATCH_COMPLETION_MARKER_FOUND")
    print("Marker path:", marker_path)

    return marker



def main():
    print("=== NORTHBRIDGE TRADEFLOW INGESTION ===")

    log_ingestion_event(
        batch_id=BATCH_ID,
        status="STARTED",
        message="Snowflake ingestion process started",
        trade_count=0
    )
    marker = verify_batch_completion()

    # Read validated trade data from Azure ADLS Gen2.
    df = load_csv_from_adls(CURATED_PATH)

    print(f"Batch ID: {BATCH_ID}")
    print(f"Validated trade records: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    # Safety check before any Snowflake ingestion.
    assert len(df) == 49, "Unexpected validated trade count."
    assert len(df.columns) == 26, "Unexpected column count."

    print("AZURE_CURATED_DATA_READY")

    # Validate trade-level integrity before Snowflake ingestion.
    if df["trade_id"].isna().any():
        raise ValueError("NULL_TRADE_IDS_DETECTED")

    if df["trade_id"].duplicated().any():
        raise ValueError("DUPLICATE_TRADE_IDS_DETECTED")

    if not df["validation_status"].eq("PASS").all():
        raise ValueError("NON_PASSED_TRADES_DETECTED")

    print("TRADE_LEVEL_INTEGRITY_PASSED")


    # Validate and retrieve the run ID from the curated data.
    run_ids = df["validation_run_id"].dropna().unique()

    if len(run_ids) != 1:
        raise ValueError(
            f"Expected one validation run ID, found {len(run_ids)}"
        )

    validation_run_id = str(run_ids[0])

    # Verify completion marker metadata against the dataset.
    if marker.get("batch_id") != BATCH_ID:
        raise ValueError("BATCH_ID_MISMATCH")

    if marker.get("status") != "COMPLETED":
        raise ValueError("BATCH_NOT_COMPLETED")

    if marker.get("validation_run_id") != validation_run_id:
        raise ValueError("VALIDATION_RUN_ID_MISMATCH")

    if marker.get("outputs", {}).get("curated") != CURATED_PATH:
        raise ValueError("CURATED_PATH_MISMATCH")

    print("BATCH_METADATA_VERIFICATION_PASSED")


    if not df["validation_status"].eq("PASS").all():
        raise ValueError("Curated dataset contains non-PASS trades.")

    print(f"Validation Run ID: {validation_run_id}")



    print("\n=== VALIDATION RUN ID CHECK ===")
    print(df["validation_run_id"].value_counts(dropna=False))

    print("\n=== VALIDATION STATUS CHECK ===")
    print(df["validation_status"].value_counts(dropna=False))



    # Connect to Snowflake and check for an existing batch.
    connection = connect_to_snowflake()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM NORTHBRIDGE_TRADEFLOW.CURATED.TRADES_VALIDATED
                WHERE VALIDATION_RUN_ID = %s
                """,
                (validation_run_id,),
            )

            existing_count = cursor.fetchone()[0]

            print(f"Existing batch records: {existing_count}")

          
            if existing_count == len(df):
                print("BATCH_ALREADY_EXISTS")
                
                log_ingestion_event(
                    batch_id=BATCH_ID,
                    status="SKIPPED",
                    message="Batch already exists in Snowflake; duplicate ingestion prevented",
                    trade_count=len(df)
                )
            
            elif existing_count == 0:
                print("BATCH_READY_FOR_INGESTION")

                ingest_validated_trades(
                    connection,
                    df,
                    validation_run_id,
                )

                log_ingestion_event(
                    batch_id=BATCH_ID,
                    status="SUCCESS",
                    message="Validated trades successfully ingested into Snowflake",
                    trade_count=len(df)
                )

            else:
                raise ValueError(
                    f"PARTIAL_OR_UNEXPECTED_BATCH: "
                    f"expected {len(df)} records, "
                    f"found {existing_count}"
                )

    finally:
        connection.close()



if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        log_ingestion_event(
            batch_id=BATCH_ID,
            status="FAILED",
            message=f"Pipeline execution failed: {type(error).__name__}: {error}",
            trade_count=0
        )
        raise
