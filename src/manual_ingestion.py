from datetime import datetime
import requests
import os

def fetch_and_store_crypto_data():
    api_url = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3/coins/markets')
    
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (BigDataBot/1.0)"
        }

        print(f"Fetching Top 100 Cryptos from {api_url}...")
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        print(f"Fetched {len(data)} assets. Storing in MongoDB Data Lake...")

        from pymongo import MongoClient
        
        mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
        mongo_pass = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'admin')
        mongo_host = 'mongo'
        mongo_port = 27017
        
        mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"
        print(f"Connecting to MongoDB at {mongo_host}...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        
        db = client["airflow_datalake"]
        collection = db["crypto_raw"]
        
        raw_document = {
            "source": "CoinGecko",
            "fetched_at": datetime.utcnow(),
            "data_points": len(data),
            "raw_data": data
        }
        
        result = collection.insert_one(raw_document)
        print(f"Data stored in MongoDB Data Lake. ID: {result.inserted_id}")
        
        client.close()
        
    except Exception as e:
        print(f"Error in crypto ingestion: {e}")

if __name__ == "__main__":
    fetch_and_store_crypto_data()
