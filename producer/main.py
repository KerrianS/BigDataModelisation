import time
import json
import os
import requests
from pymongo import MongoClient
from datetime import datetime

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongo:27017/')
API_URL = "https://api.coincap.io/v2/assets"
ASSETS = ["bitcoin", "ethereum", "solana", "cardano", "ripple"]

def get_mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client.datalake
    return db.crypto_raw

def fetch_crypto_data():
    try:
        response = requests.get(API_URL, params={"ids": ",".join(ASSETS)})
        if response.status_code == 200:
            return response.json()['data']
        else:
            print(f"Error fetching data: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching data: {e}")
        return []

def main():
    collection = get_mongo_collection()
    print("Starting Data Ingestion to MongoDB...")
    
    while True:
        assets = fetch_crypto_data()
        if assets:
            # Add ingestion timestamp
            timestamp = datetime.now().isoformat()
            for asset in assets:
                asset['ingestion_timestamp'] = timestamp
            
            # Insert into MongoDB
            result = collection.insert_many(assets)
            print(f"Inserted {len(result.inserted_ids)} documents into MongoDB at {timestamp}")
        
        time.sleep(10) # API Limit friendly

if __name__ == "__main__":
    main()
