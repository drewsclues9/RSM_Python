import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
import numpy as np
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import warnings
import gzip
# Suppress the specific pandas warning
warnings.filterwarnings("ignore", message="Pandas Dataframe has non-standard index")
load_dotenv('C:/Users/E075882/OneDrive - RSM/All Data/Client/Galaxy/python/keys.env')
# Load credentials from environment variables
tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")
user = os.getenv("USER")
account = os.getenv("ACCOUNT")
secret_name = os.getenv("SECRET_NAME")
vault_url = os.getenv("VAULT_URL")
# Ensure that environment variables are set
if not all([tenant_id, client_id, client_secret, user, account, secret_name, vault_url]):
    raise ValueError("Missing values in environment variables!")

# Authenticate using ClientSecretCredential
credential = ClientSecretCredential(tenant_id, client_id, client_secret)

# Create a SecretClient instance
client = SecretClient(vault_url=vault_url, credential=credential)

private_key_path = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/Galaxy/python/private_key.pem'

with open(private_key_path, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
        backend=default_backend()
    )

# Convert to PEM format required by connector
private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

def count_gz_csv_rows(filepath):
    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
        return sum(1 for line in f) - 1  # subtract 1 for header

# Snowflake connection parameters
SNOWFLAKE_CONFIG = {
    "user": user,
    "private_key": private_key_bytes,
    "account": account,  
    "warehouse": "COMPUTE_WH",
    "database": "GALAXY",
    "schema": "MIGRATION",
    "role": "SERVICE_MIGRATION"
}
# Connect to Snowflake
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
cur = conn.cursor()


# Query the Staging Table Lookup
mapping_query = "SELECT * FROM STG_TBL_LOOKUP;"
cur.execute(mapping_query)

# Fetch data and convert it into a DataFrame
columns = ['SNOWFLAKE_TABLE','SAP_TABLE']  # Get column names
mapdf = pd.DataFrame(cur.fetchall(), columns=columns)  # Create DataFrame


folder_path = 'C:/Users/E075882/RSM/Project Galaxy - External Project Documents/DDS/Data Migration/01- Data Extracts/SFTP Loading/FilesToLoad/Staging/'
archive_folder_path = "C:/Users/E075882/RSM/Project Galaxy - External Project Documents/DDS/Data Migration/01- Data Extracts/SFTP Loading/FilesLoaded"
stage_name = "@MIGR_INGESTION"



for index, row in mapdf.iterrows():
    sap_table = row['SAP_TABLE']
    table_name = row['SNOWFLAKE_TABLE']

    for filename in os.listdir(folder_path):
        if sap_table in filename:
            
            print(f"Processing: {filename}")
            csv_file_path = os.path.join(folder_path, filename)
            quoted_file_path = f"'file://{csv_file_path}'"
                        
            if cur.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name.upper()}'").fetchone()[0] == 0:
                df = pd.read_csv(csv_file_path, dtype=str, compression='gzip')
                columns = [f'"{col}" VARCHAR(99999)' for col in df.columns]
                create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)});"
                cur.execute(create_table_query)

            # Write chunk to Snowflake
            try:
            # Step 1: Upload the file to Snowflake stage
                cur.execute(f"PUT {quoted_file_path} {stage_name} AUTO_COMPRESS=FALSE")
                
                # Step 2: Copy data into the table (Snowflake decompresses gzip automatically)
                cur.execute(f"""
                    COPY INTO {table_name}
                    FROM {stage_name}
                    FILES = ('{filename}')
                    FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '\"' SKIP_HEADER = 1 TRIM_SPACE = TRUE)
                    ON_ERROR = 'CONTINUE'
                """)
                num_rows = count_gz_csv_rows(csv_file_path)
                # Audit log
                sql = f"""
                    INSERT INTO AUDITLOG(FILENAME, TABLENAME, RECORDCOUNT, LOADTIME)
                    VALUES ('{filename}', '{table_name}', {num_rows}, CURRENT_TIMESTAMP)
                """
                cur.execute(sql)

                print(f"Uploaded {num_rows} rows from {filename} to {table_name}")
                # Archive file
                dest_file_path = os.path.join(archive_folder_path, filename)
                src_file_path = os.path.join(folder_path, filename)
                if os.path.exists(dest_file_path):
                    os.remove(dest_file_path)
                    print(f"Existing file at {dest_file_path} has been removed.")
                os.rename(src_file_path, dest_file_path)

                print("File moved successfully!")
            except Exception as e:
                print(f"An error occurred: {e}")
            
                


# Close connection

cur.close()
conn.close()

print("All files successfully uploaded to Snowflake.")
