from pymongo import MongoClient
import os
import pprint

try:
    client = MongoClient("mongodb://admin:admin@mongo:27017/", serverSelectionTimeoutMS=2000)
    client.server_info()
    print("Connected via Docker network (host: mongo)")
except:
    print("Docker connection failed, trying localhost...")
    client = MongoClient("mongodb://admin:admin@localhost:27017/")

db = client["airflow_datalake"]
collection = db["crypto_raw"]

print("--- MongoDB Data Lake Verification ---")
count = collection.count_documents({})
print(f"Total Documents in 'crypto_raw': {count}")

if count > 0:
    print("\nMost recent document:")
    latest_doc = collection.find_one(sort=[("fetched_at", -1)])
    data_sample = latest_doc.copy()
    raw_data = data_sample.pop('raw_data', [])
    pprint.pprint(data_sample)
    print(f"Raw Data (First 2 items): {raw_data[:2]}")
else:
    print("No data found yet. Wait for the Airflow DAG to run.")
