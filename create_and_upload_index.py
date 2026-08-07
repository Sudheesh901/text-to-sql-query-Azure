import os
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField,SearchableField
from azure.search.documents import SearchClient
load_dotenv()

endpoint=os.getenv("AZURE_SEARCH_ENDPOINT")
key=os.getenv("AZURE_SEARCH_KEY")
index_name=os.getenv("INDEX_NAME")
deployment=os.getenv("TEXT_EMBEDDING_MODEL")
api_version=os.getenv("SEARCH_API_VERSION")

client=SearchIndexClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

if index_name in [idx.name for idx in client.list_indexes()]:
    client.delete_index(index_name)

# Define Fields

fields = [
    SimpleField(name="id", type="Edm.String", key=True, searchable=False),
    SearchableField(name="type", type="Edm.String", filterable=True, searchable=True, analyzer_name="standard.lucene"),
    SearchableField(name="name", type="Edm.String", sortable=True, analyzer_name="standard.lucene"),
    SearchableField(name="description", type="Edm.String", sortable=True, analyzer_name="standard.lucene"),
    SearchableField(name="columns", type="Edm.String", sortable=True, analyzer_name="standard.lucene"),
]

# Create Index
index= SearchIndex(name=index_name, fields=fields)
client.create_index(index)
print(f"Created Index: {index_name}")


#load _csv

df = pd.read_csv("data/aaitech_vector_schema_info.csv")
df=df.fillna("")


#Intialise Search Clinet - using client to upload the document
search_client=SearchClient(
    endpoint=endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(key)
)

#prepare and clean documents
documents = []
for _,row in df.iterrows():
    doc={
        "id":str(row["id"]),
        "type":str(row["type"]),
        "name":str(row["name"]),
        "description":str(row["description"]),
        "columns":str(row["columns"])
    }
    documents.append(doc)

#Upload the documents
result = search_client.upload_documents(documents=documents)
print(f"Uploaded {len(documents)} documents")