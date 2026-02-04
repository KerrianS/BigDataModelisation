from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import os

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
    description='Fetch crypto data from CoinCap API and store in Postgres',
    schedule_interval=timedelta(minutes=10),
    catchup=False
)

def fetch_and_store_crypto_data():
    """Fetch crypto data from CoinCap API and insert into Postgres"""
    
    # API Configuration
    api_url = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3/coins/markets')
    # API Configuration
    api_url = os.getenv('COINGECKO_API_URL', 'https://api.coingecko.com/api/v3/coins/markets')
    
    # BIG DATA MODE: Fetch Top 100 coins instead of fixed list
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }
    
    # Database Configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'postgres'),
        'database': os.getenv('DB_NAME', 'airflow'),
        'user': os.getenv('DB_USER', 'airflow'),
        'password': os.getenv('DB_PASSWORD', 'airflow')
    }
    
    try:
        # Fetch data from API
        headers = {
            "User-Agent": "Mozilla/5.0 (BigDataBot/1.0)"
        }

        print(f"Fetching Top 100 Cryptos from {api_url}...")
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        print(f"Fetched {len(data)} assets. Preparing Big Data ingestion...")
        
        # Connect to Postgres
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Schema Evolution: Drop old table to enforce new Big Data schema
        # In production, we would use ALTER TABLE or migration scripts
        cur.execute("DROP TABLE IF EXISTS crypto_prices")
        
        # Create detailed table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id SERIAL PRIMARY KEY,
                asset_id VARCHAR(100),
                symbol VARCHAR(20),
                name VARCHAR(100),
                price_usd NUMERIC(24, 8),
                market_cap_usd NUMERIC(24, 2),
                volume_24h_usd NUMERIC(24, 2),
                change_percent_24h NUMERIC(10, 4),
                high_24h NUMERIC(24, 8),
                low_24h NUMERIC(24, 8),
                ath NUMERIC(24, 8),
                ath_change_percentage NUMERIC(10, 4),
                circulating_supply NUMERIC(24, 2),
                total_supply NUMERIC(24, 2),
                rank INT,
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Batch Insert for better performance
        # Using execute_batch would be even better for "Big Data", but simple loop is fine for 100 rows
        for asset in data:
            cur.execute("""
                INSERT INTO crypto_prices 
                (asset_id, symbol, name, price_usd, market_cap_usd, volume_24h_usd, change_percent_24h,
                 high_24h, low_24h, ath, ath_change_percentage, circulating_supply, total_supply, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                asset.get('id'),
                asset.get('symbol'),
                asset.get('name'),
                float(asset.get('current_price') or 0),
                float(asset.get('market_cap') or 0),
                float(asset.get('total_volume') or 0),
                float(asset.get('price_change_percentage_24h') or 0),
                float(asset.get('high_24h') or 0),
                float(asset.get('low_24h') or 0),
                float(asset.get('ath') or 0),
                float(asset.get('ath_change_percentage') or 0),
                float(asset.get('circulating_supply') or 0),
                float(asset.get('total_supply') or 0),
                int(asset.get('market_cap_rank') or 0)
            ))
        
        conn.commit()
        print(f"Successfully inserted {len(data)} records into crypto_prices table")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error in crypto ingestion: {e}")
        raise e

# Define task
fetch_crypto_task = PythonOperator(
    task_id='fetch_and_store_crypto',
    python_callable=fetch_and_store_crypto_data,
    dag=dag,
)

fetch_crypto_task
