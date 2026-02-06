from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import os
import time

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'crypto_ingestion_pipeline',
    default_args=default_args,
    description='Fetch crypto data with automated backfill',
    schedule_interval=timedelta(minutes=3),
    catchup=False
)

def check_and_backfill_data():
    """Detect gaps in data and fetch historical data from CoinGecko if needed."""
    from sqlalchemy import create_engine, text
    from pymongo import MongoClient
    
    # Configuration
    pg_url = os.getenv('AIRFLOW__DATABASE__SQL_ALCHEMY_CONN')
    mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
    mongo_pass = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'admin')
    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@mongo:27017/"
    crypto_list = os.getenv('CRYPTO_ASSETS', 'bitcoin,ethereum,solana').split(',')
    
    try:
        engine = create_engine(pg_url)
        with engine.connect() as conn:
            # Check the last timestamp in the database
            query = text("SELECT MAX(ingestion_timestamp) FROM crypto_prices")
            result = conn.execute(query).fetchone()
            last_timestamp = result[0] if result and result[0] else None
            
        now = datetime.utcnow()
        gap_limit = timedelta(minutes=15)
        
        if last_timestamp and (now - last_timestamp) > gap_limit:
            print(f"Gap detected! Last data was from {last_timestamp}. Backfilling...")
            
            client = MongoClient(mongo_uri)
            db = client["airflow_datalake"]
            collection = db["crypto_raw"]
            
            # Calculate days to fetch (max 30 days for safety)
            diff = now - last_timestamp
            days_to_fetch = min(max(1, diff.days + 1), 30)
            
            for crypto_id in crypto_list:
                print(f"Fetching history for {crypto_id}...")
                history_url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
                params = {
                    "vs_currency": "usd",
                    "days": days_to_fetch
                }
                
                resp = requests.get(history_url, params=params)
                if resp.status_code == 200:
                    hist_data = resp.json()
                    prices = hist_data.get('prices', [])
                    
                    # Convert historical points to the format expected by Spark
                    for p in prices:
                        ts_ms, price = p[0], p[1]
                        dt_point = datetime.utcfromtimestamp(ts_ms / 1000.0)
                        
                        # Only backfill points AFTER our last timestamp
                        if dt_point > last_timestamp:
                            backfill_doc = {
                                "source": "CoinGecko-Backfill",
                                "fetched_at": dt_point,
                                "raw_data": [{
                                    "id": crypto_id,
                                    "symbol": crypto_id[:3], # Fallback symbol
                                    "name": crypto_id.capitalize(),
                                    "current_price": price,
                                    "market_cap": 0,
                                    "total_volume": 0,
                                    "ingestion_timestamp": dt_point # Pass through
                                }]
                            }
                            collection.insert_one(backfill_doc)
                
                # Respect Rate Limits
                time.sleep(1) 
            
            client.close()
        else:
            print("No significant gap detected.")
            
    except Exception as e:
        print(f"Backfill skip or error: {e}")

def fetch_and_store_crypto_data():
    api_url = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3/coins/markets')
    params = { "vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1, "sparkline": "false" }
    
    try:
        headers = { "User-Agent": "Mozilla/5.0 (BigDataBot/1.0)" }
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        from pymongo import MongoClient
        mongo_user, mongo_pass = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin'), os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'admin')
        mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@mongo:27017/"
        client = MongoClient(mongo_uri)
        db, collection = client["airflow_datalake"], client["airflow_datalake"]["crypto_raw"]
        
        collection.insert_one({
            "source": "CoinGecko",
            "fetched_at": datetime.utcnow(),
            "data_points": len(data),
            "raw_data": data
        })
        client.close()
    except Exception as e:
        print(f"Error in crypto ingestion: {e}")
        raise e

backfill_task = PythonOperator(
    task_id='check_and_backfill',
    python_callable=check_and_backfill_data,
    dag=dag,
)

fetch_crypto_task = PythonOperator(
    task_id='fetch_and_store_crypto',
    python_callable=fetch_and_store_crypto_data,
    dag=dag,
)

backfill_task >> fetch_crypto_task
