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
import time
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

start_time = time.time()

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
columns = ['SNOWFLAKE_TABLE','STG_TBL', 'LAST_MODIFIED_COLUMN', 'RUN_DATE', 'KEYS']  # Include More column names here
mapdf = pd.DataFrame(cur.fetchall(), columns=columns)  # Create DataFrame



for index, row in mapdf.iterrows():
    tgt = row['SNOWFLAKE_TABLE']
    src = row['STG_TBL']
    last_mod = row['LAST_MODIFIED_COLUMN']
    run_dt = row['RUN_DATE']
    keys = row['KEYS']
    #check that stg tbl exists 
    query = f'SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME={src}'
    cur.execute(query)
    result = cur.fetchone()
    #if stg tbl does not exist, we skip load process and move on
    if result[0] > 0:
        #if no key specificed, it is just a full trunc reload using merge stored procedure
        if keys == '':
            query = f'TRUNCATE TABLE {tgt}'
            cur.execute(query)
            print(f'{tgt} truncated')

        query = f'CALL DELTA_MERGE({tgt}, {src}, {run_dt}, {last_mod}, {keys})'

        cur.execute(query)

        print(f'{tgt} successfully merged')
    else:
        print(f'{src} does not exist for {tgt}')

print('All tables merged')

end_time = time.time()
elapsed_time = end_time - start_time

print(f"Script executed in {elapsed_time:.2f} seconds.")
