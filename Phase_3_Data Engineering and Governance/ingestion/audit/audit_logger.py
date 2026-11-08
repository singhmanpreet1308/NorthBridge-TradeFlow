
import json
from datetime import datetime, timezone
from pathlib import Path


AUDIT_FILE = Path(__file__).parent / "ingestion_audit.jsonl"



def log_ingestion_event(batch_id, status, message, trade_count=0):
    """Append an ingestion event to the local audit log."""

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "status": status,
        "message": message,
        "trade_count": trade_count,
    }

    with AUDIT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")

    print(f"AUDIT_LOGGED: {status}")


def main():
    log_ingestion_event(
        batch_id= BATCH_ID,
        status="STARTED",
        message="Snowflake ingestion process started",
        trade_count=0
    )

    # Keep all your existing main() code below this line

