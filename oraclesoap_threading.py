from concurrent.futures import ThreadPoolExecutor
import requests
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
import xml.etree.ElementTree as ET
import base64
import pandas as pd

# Define your authentication credentials
username = 'mdoty.con@akebia.com'
password = 'Cloud2024!'

# Set up a session with basic authentication
session = requests.Session()
session.auth = HTTPBasicAuth(username, password)

# Create a Zeep client with the session
client = Client('https://edlk-test.fa.us2.oraclecloud.com/fscmService/ErpIntegrationService?WSDL',
                transport=Transport(session=session))

# Read in the list of document numbers from Excel
excel_file = 'C:\\Users\\E075882\\Downloads\\RSM PO Doc Report_RSM PO Doc Report NEW.xlsx'
df = pd.read_excel(excel_file)
doc_numbers = df['DOCUMENT_ID'].tolist()

# Function to download document for a given document number
def download_document(doc_number):
    try:
        response = client.service.getDocumentForDocumentId(str(int(doc_number)))
        print(doc_number)
        doc_id = response['DocumentId']
        doc_nm = response['DocumentName']
        decoded_content = base64.b64decode(response['Content'])
        with open(f"C:\\Users\\E075882\\OneDrive - RSM\\All Data\\Client\\python\\SOAP Files\\{doc_id}_{doc_nm}", "wb") as f:
            f.write(decoded_content)
    except Exception as e:
        print(f"An exception occurred for document {doc_number}: {str(e)}")

# Define the number of threads for concurrent processing
num_threads = 10  # You can adjust this value based on your system's capabilities

# Use a ThreadPoolExecutor to execute the download_document function concurrently
with ThreadPoolExecutor(max_workers=num_threads) as executor:
    executor.map(download_document, doc_numbers)
