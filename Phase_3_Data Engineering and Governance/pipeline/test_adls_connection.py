
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# Azure configuration
STORAGE_ACCOUNT = "stnorthbridgetradeflow"
FILE_SYSTEM = "northbridge-tradeflow"

ACCOUNT_URL = f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net"

def test_connection():
    try:
        credential = AzureCliCredential()

        service_client = DataLakeServiceClient(
            account_url=ACCOUNT_URL,
            credential=credential
        )

        filesystem_client = service_client.get_file_system_client(
            file_system=FILE_SYSTEM
        )

        print("Connected to Azure Data Lake Storage Gen2")
        print("\nAvailable directories and files:")

        for path in filesystem_client.get_paths():
            print(f" - {path.name}")

    except Exception as error:
        print(f"Connection failed: {error}")
        raise


if __name__ == "__main__":
    test_connection()
