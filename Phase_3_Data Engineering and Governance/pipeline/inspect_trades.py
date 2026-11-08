
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

STORAGE_ACCOUNT = "stnorthbridgetradeflow"
FILE_SYSTEM = "northbridge-tradeflow"
FILE_PATH = "raw/trades/sample_trades.csv"

credential = AzureCliCredential()

service = DataLakeServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net",
    credential=credential
)

filesystem = service.get_file_system_client(FILE_SYSTEM)
file_client = filesystem.get_file_client(FILE_PATH)

# Download CSV directly from Azure
file_bytes = file_client.download_file().readall()

# Read into Pandas
df = pd.read_csv(io.BytesIO(file_bytes))

print("\n=== DATASET INSPECTION ===")
print("SHAPE:", df.shape)

print("\nCOLUMNS:")
print(df.columns.tolist())

print("\nDATA TYPES:")
print(df.dtypes.to_string())

print("\nNULL COUNTS:")
print(df.isnull().sum().to_string())

print("\nDUPLICATE ROWS:")
print(df.duplicated().sum())

print("\nT-1001 RECORDS:")
if "trade_id" in df.columns:
    print(df[df["trade_id"].astype(str) == "T-1001"].to_string(index=False))
else:
    print("Trade ID column needs to be identified.")


print("\n=== TRADE VERSION VALIDATION ===")

duplicate_versions = df.duplicated(
    subset=["trade_id", "trade_version"]
).sum()

print("Duplicate trade/version keys:", duplicate_versions)

print("\nTrade version distribution:")
print(df["trade_version"].value_counts().sort_index())

print("\nTrade status distribution:")
print(df["trade_status"].value_counts(dropna=False))

print("\n=== T-1001 GOLDEN THREAD ===")

t1001 = df[df["trade_id"] == "T-1001"]

print(t1001[
    [
        "trade_id",
        "trade_version",
        "notional_amount",
        "currency",
        "trade_status",
        "amendment_reason"
    ]
].to_string(index=False))

