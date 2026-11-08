
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

STORAGE_ACCOUNT = "stnorthbridgetradeflow"
FILE_SYSTEM = "northbridge-tradeflow"
SOURCE_PATH = "raw/trades/sample_trades.csv"

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"


def ingest_trades():
    run_id = f"RUN-{uuid4().hex[:12].upper()}"
    ingested_at = datetime.now(timezone.utc).isoformat()

    credential = AzureCliCredential()

    service = DataLakeServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net",
        credential=credential
    )

    filesystem = service.get_file_system_client(FILE_SYSTEM)
    file_client = filesystem.get_file_client(SOURCE_PATH)

    # Download original source bytes
    source_bytes = file_client.download_file().readall()

    # Calculate source checksum
    checksum = hashlib.sha256(source_bytes).hexdigest()

    # Read CSV without changing original data
    source_text = source_bytes.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(source_text))
    rows = list(reader)

    audit_record = {
        "run_id": run_id,
        "source_file": SOURCE_PATH,
        "ingested_at": ingested_at,
        "sha256": checksum,
        "record_count": len(rows),
        "pipeline_status": "INGESTED"
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_path = LOG_DIR / f"{run_id}.json"

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(audit_record, file, indent=4)

    print("\n=== NorthBridge TradeFlow Ingestion ===")
    print(f"Run ID: {run_id}")
    print(f"Source: {SOURCE_PATH}")
    print(f"Records: {len(rows)}")
    print(f"SHA-256: {checksum}")
    print(f"Status: INGESTED")
    print(f"Audit log: {log_path}")

    return rows, audit_record


if __name__ == "__main__":
    ingest_trades()
