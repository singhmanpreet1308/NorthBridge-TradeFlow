
import os
from getpass import getpass
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization

# Use your actual Snowflake organization and account names.
ORGANIZATION = "LYUDTKG"
ACCOUNT = "OC94773"

PRIVATE_KEY_PATH = (
    Path.home() / ".snowflake" / "northbridge_rsa_key.pem"
)

# Read the passphrase securely without displaying it.
passphrase = getpass("Enter RSA private key passphrase: ")

with open(PRIVATE_KEY_PATH, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=passphrase.encode("utf-8"),
    )

# Convert the key into the format required by Snowflake.
private_key_der = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

connection = None

try:
    connection = snowflake.connector.connect(
        account=f"{ORGANIZATION}-{ACCOUNT}",
        user="NORTHBRIDGE_INGEST_USER",
        private_key=private_key_der,
        role="NORTHBRIDGE_INGEST_ROLE",
        warehouse="NORTHBRIDGE_WH",
        database="NORTHBRIDGE_TRADEFLOW",
        schema="STAGING",
        session_parameters={
            "QUERY_TAG": "NORTHBRIDGE_KEYPAIR_TEST"
        },
    )

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                CURRENT_USER(),
                CURRENT_ROLE(),
                CURRENT_DATABASE(),
                CURRENT_SCHEMA()
        """)

        result = cursor.fetchone()

        print("\nSNOWFLAKE_CONNECTION_SUCCESS")
        print("User:", result[0])
        print("Role:", result[1])
        print("Database:", result[2])
        print("Schema:", result[3])

finally:
    if connection is not None:
        connection.close()
