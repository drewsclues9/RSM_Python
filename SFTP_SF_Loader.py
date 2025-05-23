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


folder_path = "C:/Users/E075882/RSM/Project Galaxy - External Project Documents/DDS/Data Migration/01- Data Extracts/SFTP Loading/FilesToLoad"
archive_folder_path = "C:/Users/E075882/RSM/Project Galaxy - External Project Documents/DDS/Data Migration/01- Data Extracts/SFTP Loading/FilesLoaded"


for index, row in mapdf.iterrows():


    i = 0

    # CSV file path
    for filename in os.listdir(folder_path):
        
        if mapdf.loc[index, 'SAP_TABLE'] in filename:
            print(mapdf.loc[index, 'SAP_TABLE'])
            print(filename)
            table_name = mapdf.loc[index, 'SNOWFLAKE_TABLE']
            csv_file_path = os.path.join(folder_path, filename)

            if '.TXT' in filename.upper():
                df = pd.read_csv(csv_file_path, delimiter="|", skiprows=3, dtype=str) #add this encoding if unicode error - encoding="latin-1"
                df.columns = df.columns.str.strip()  # Clean column names
                df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
                #Drop unnamed columns
                df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
                # Remove the first row (index 0) after the headers
                df = df.iloc[1:].reset_index(drop=True)
            if '.CSV' in filename.upper():
                chunk_size = 100_000  # adjust as needed
                cleaned_chunks = []
                for chunk in pd.read_csv(csv_file_path, dtype=str, chunksize=chunk_size):
                # Strip column names
                    chunk.columns = chunk.columns.str.strip()
                # Strip string values only for object columns
                    for col in chunk.select_dtypes(include="object").columns:
                        chunk[col] = chunk[col].str.strip()
                # Remove unnamed columns
                    chunk = chunk.loc[:, ~chunk.columns.str.contains("^Unnamed")]
                    cleaned_chunks.append(chunk)
                # Optionally combine all chunks into one DataFrame (if your system can handle it)
                    df = pd.concat(cleaned_chunks, ignore_index=True)                  
            if '.XLSX' in filename.upper():
                # Read the CSV into a pandas DataFrame
                df = pd.read_excel(csv_file_path, dtype=str)
                #Drop unnamed columns
                df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            # Force all columns to STRING
            df = df.astype(str)
            #remove leading and trailing whitespace from field names
            #df.columns = df.columns.str.strip()
            # Convert possible string 'nan' values to real NaN
            df.replace(["nan", "NaN", "None"], np.nan, inplace=True)
            # Fill NaN with an empty string (or another default value)
            df.fillna("", inplace=True) 
            #CREATE TABLE IF NOT EXISTS
            if i == 0:
                columns = [f'"{col}" VARCHAR(99999)' for col in df.columns] 
                create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)});"
                cur.execute(create_table_query)
            count = len(df)

            # Write DataFrame to Snowflake
            success, num_chunks, num_rows, output = write_pandas(conn, df, table_name)
            sql = f"INSERT INTO AUDITLOG(FILENAME, TABLENAME, RECORDCOUNT, LOADTIME) VALUES ('{filename}', '{table_name}', {count}, CURRENT_TIMESTAMP)"
            cur.execute(sql)
            # Print upload results
            print(f"Success: {success}, Rows Inserted: {num_rows}")
            i = i + 1

            # Archive file
            dest_file_path = os.path.join(archive_folder_path, filename)
            src_file_path = os.path.join(folder_path, filename)
            if os.path.exists(dest_file_path):
                os.remove(dest_file_path)
                print(f"Existing file at {dest_file_path} has been removed.")
            os.rename(src_file_path, dest_file_path)

            print("File moved successfully!")


# Close connection
conn.close()

print("All files successfully uploaded to Snowflake.")
