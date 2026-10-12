
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

STORAGE_ACCOUNT = "stnorthbridgetradeflow"
FILE_SYSTEM = "northbridge-tradeflow"

credential = AzureCliCredential()

service = DataLakeServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net",
    credential=credential
)

filesystem = service.get_file_system_client(FILE_SYSTEM)

files = {
    "Confirmations": "raw/confirmations/independent_confirmations.csv",
    "Error Manifest": "raw/reference/seeded_error_manifest.csv",
    "Seeded Errors": "raw/reference/seeded_errors.csv"
}

for name, path in files.items():
    print(f"\n{'=' * 50}")
    print(name.upper())
    print(f"{'=' * 50}")

    file_client = filesystem.get_file_client(path)
    file_bytes = file_client.download_file().readall()

    df = pd.read_csv(io.BytesIO(file_bytes))

    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nNull counts:")
    print(df.isnull().sum().to_string())

    print("\nFirst 5 records:")
    print(df.head().to_string(index=False))

    if "trade_id" in df.columns:
        print("\nT-1001 records:")
        print(
            df[df["trade_id"].astype(str) == "T-1001"]
            .to_string(index=False)
        )


# Display every expected seeded validation rule
manifest_path = "raw/reference/seeded_error_manifest.csv"

manifest_bytes = (
    filesystem
    .get_file_client(manifest_path)
    .download_file()
    .readall()
)

manifest = pd.read_csv(io.BytesIO(manifest_bytes))

print("\n=== COMPLETE ERROR MANIFEST ===")
print(manifest.to_string(index=False))

print("\n=== DQ-007 FIXED RATE CHECK ===")

seeded_bytes = (
    filesystem
    .get_file_client("raw/reference/seeded_errors.csv")
    .download_file()
    .readall()
)

seeded_df = pd.read_csv(io.BytesIO(seeded_bytes))

print(
    seeded_df.loc[
        seeded_df["trade_id"] == "T-1020",
        ["trade_id", "fixed_rate"]
    ].to_string(index=False)
)
