import os
import requests
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def manual_backfill(days=1, crypto_list=None):
    """
    Manually fetch historical data and inject it into the pipeline.
    """
    # 1. Config
    if not crypto_list:
        crypto_list = os.getenv('CRYPTO_ASSETS', 'bitcoin,ethereum,solana').split(',')
    
    mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
    mongo_pass = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'admin')
    mongo_host = 'localhost' # External access
    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:27017/"
    
    print(f"🚀 Starting manual backfill for {days} days...")
    print(f"📦 Target assets: {crypto_list}")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["airflow_datalake"]
        collection = db["crypto_raw"]
        
        for crypto_id in crypto_list:
            print(f"\n--- Fetching {crypto_id} ---")
            history_url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days
            }
            
            resp = requests.get(history_url, params=params)
            if resp.status_code == 200:
                hist_data = resp.json()
                prices = hist_data.get('prices', [])
                print(f"✅ Found {len(prices)} data points.")
                
                count = 0
                for p in prices:
                    ts_ms, price = p[0], p[1]
                    dt_point = datetime.utcfromtimestamp(ts_ms / 1000.0)
                    
                    backfill_doc = {
                        "source": "Manual-Backfill",
                        "fetched_at": dt_point,
                        "raw_data": [{
                            "id": crypto_id,
                            "symbol": crypto_id[:3],
                            "name": crypto_id.capitalize(),
                            "current_price": price,
                            "market_cap": 0,
                            "total_volume": 0,
                            "ingestion_timestamp": dt_point
                        }]
                    }
                    collection.insert_one(backfill_doc)
                    count += 1
                
                print(f"💾 Injected {count} points for {crypto_id}.")
            else:
                print(f"❌ Error fetching {crypto_id}: {resp.status_code}")
                print(f"Response: {resp.text}")
            
            # Rate limit safety
            time.sleep(2)

        client.close()
        print("\n✨ Manual backfill complete! Data is now flowing through Kafka and Spark.")

    except Exception as e:
        print(f"❌ Critical error: {e}")

if __name__ == "__main__":
    import sys
    days_arg = 1
    if len(sys.argv) > 1:
        try:
            days_arg = int(sys.argv[1])
        except ValueError:
            print("Invalid number of days. Defaulting to 1.")
            
    manual_backfill(days=days_arg)
