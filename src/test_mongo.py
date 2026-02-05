from pymongo import MongoClient
from datetime import datetime

mongo_uri = "mongodb://admin:admin@mongo:27017/"
print(f"Connecting to: {mongo_uri}")

client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

try:
    client.server_info()
    print("MongoDB connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

db = client["airflow_datalake"]
collection = db["crypto_raw"]

test_doc = {
    "source": "TEST",
    "fetched_at": datetime.utcnow(),
    "data_points": 1,
    "raw_data": [{"test": "data"}]
}

result = collection.insert_one(test_doc)
print(f"Test document inserted with ID: {result.inserted_id}")

count = collection.count_documents({})
print(f"Total documents in collection: {count}")

latest = collection.find_one(sort=[("fetched_at", -1)])
print(f"Latest document: {latest}")

client.close()
