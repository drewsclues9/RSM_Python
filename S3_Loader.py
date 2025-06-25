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
import re
import io
import boto3
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
aws_key=os.getenv("AWS_ACCESS_KEY")
aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY")
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



# Snowflake connection parameters
SNOWFLAKE_CONFIG = {
    "user": user,
    "private_key": private_key_bytes,
    "account": account,  
    "warehouse": "COMPUTE_WH_LARGE",
    "database": "GALAXY",
    "schema": "MIGRATION",
    "role": "SERVICE_MIGRATION"
}
# Connect to Snowflake
conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
cur = conn.cursor()

# Get mapping
audit_table = 'AUDITLOG'
# Query the Staging Table Lookup
mapping_query = "SELECT * FROM STG_TBL_LOOKUP;"
cur.execute(mapping_query)

# Fetch data and convert it into a DataFrame
columns = ['SNOWFLAKE_TABLE','SAP_TABLE']  # Get column names
mapdf = pd.DataFrame(cur.fetchall(), columns=columns)  # Create DataFrame

# Get already loaded files
cur.execute(f"SELECT FILENAME FROM {audit_table}")
loaded_files = {row[0] for row in cur.fetchall()}

# List files in S3
stage_name = 'MIGR_S3'
s3_bucket = 'sparc-rsm-migration-conversion-01'
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_key,
    aws_secret_access_key=aws_secret_key,
    region_name='us-east-1'  # adjust if needed
)
response = s3.list_objects_v2(Bucket=s3_bucket)
files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.csv.gz') and not obj['Key'].startswith('archive/')]

for index, row in mapdf.iterrows():
    sap_table = row['SAP_TABLE']
    table_name = row['SNOWFLAKE_TABLE']
    for file_key in files:
        filename = os.path.basename(file_key)
        if filename in loaded_files:
           # print(f'{filename} already loaded')
            continue  # skip already loaded

        match = re.match(r"^([A-Z0-9_]+)_", filename)
        
       
        parts = filename.split('_', 1)
        prefix = parts[0] + '_' if len(parts) > 1 else ''
        
        s = filename.strip()
        n = len(sap_table)
        left = s[:n]
        if sap_table == left:
            
            meta = s3.head_object(Bucket=s3_bucket, Key=file_key)
            file_size = meta['ContentLength']
            if file_size < 100:
                print(f"Skipping file {filename}: too small ({file_size} bytes)")
                continue
            if cur.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name.upper()}'").fetchone()[0] == 0:
                        local_path = 'C:/Users/E075882/OneDrive - RSM/All Data/Client/Galaxy/Extracts/schema.csv.gz'
                        s3.download_file(s3_bucket, file_key, local_path)
                        df = pd.read_csv(local_path, dtype=str, compression='gzip', encoding="ISO-8859-1")
                        columns = [f'"{col}" VARCHAR(99999)' for col in df.columns]
                        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)});"
                        cur.execute(create_table_query)
                        print(f'created table {table_name}')
            
            
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count_before = cur.fetchone()[0]
            # Load data
            try:
                cur.execute(f"""
                    COPY INTO {table_name}
                    FROM '@{stage_name}/{file_key}'
                    FILE_FORMAT=(TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '\"' SKIP_HEADER = 1 TRIM_SPACE = TRUE)
                    ON_ERROR='CONTINUE';
                """)
                # Get row count after loading
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count_after = cur.fetchone()[0]
                num_rows = row_count_after - row_count_before
                # Log load
                sql = f"""
                                INSERT INTO AUDITLOG(FILENAME, TABLENAME, RECORDCOUNT, LOADTIME)
                                VALUES ('{filename}', '{table_name}', {num_rows}, CURRENT_TIMESTAMP)
                            """
                cur.execute(sql)

                print(f"Loaded: {filename} → {table_name}")
            except:
                 print(f'issue with {filename}')

cur.close()
conn.close()
