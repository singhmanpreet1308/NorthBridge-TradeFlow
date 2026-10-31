
import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]

source_path = PROJECT_ROOT /"Phase_3_Data_Engineering"/"azure_backup"/"raw"/"trades"/"sample_trades.csv"
approval_path = BASE_DIR / "T1001_Approval.json"
output_path = BASE_DIR / "T1001_v2.csv"

# Read source trades and approval evidence.
trades = pd.read_csv(source_path)
approval = json.loads(approval_path.read_text(encoding="utf-8"))

# Confirm approval and original trade.
if approval["approval_status"] != "APPROVED":
    raise ValueError("Amendment has not been approved.")

original = trades.loc[
    (trades["trade_id"] == "T-1001")
    & (trades["trade_version"] == 1)
]

if len(original) != 1:
    raise ValueError("Expected exactly one T-1001 version 1.")

# Preserve original fields.
amended = original.copy()

# Apply approved correction.
amended.loc[:, "trade_version"] = 2
amended.loc[:, "notional_amount"] = 10000000
amended.loc[:, "trade_status"] = "AMENDED"
amended["amendment_reason"] = amended["amendment_reason"].astype("string")
amended["amendment_reason"] = "DEMO_NOTIONAL_MISMATCH"
amended.loc[:, "record_timestamp"] = datetime.now(
    timezone.utc
).isoformat()

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
