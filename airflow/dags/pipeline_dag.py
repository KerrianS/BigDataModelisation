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
    api_url = os.getenv('COINCAP_API_URL', 'https://api.coincap.io/v2/assets')
    assets = os.getenv('CRYPTO_ASSETS', 'bitcoin,ethereum,solana').split(',')
    
    # Database Configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'postgres'),
        'database': os.getenv('DB_NAME', 'airflow'),
        'user': os.getenv('DB_USER', 'airflow'),
        'password': os.getenv('DB_PASSWORD', 'airflow')
    }
    
    try:
        # Fetch data from API
        response = requests.get(api_url, params={"ids": ",".join(assets)})
        response.raise_for_status()
        data = response.json()['data']
        
        print(f"Fetched {len(data)} crypto assets from API")
        
        # Connect to Postgres
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Create table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id SERIAL PRIMARY KEY,
                asset_id VARCHAR(50),
                symbol VARCHAR(20),
                name VARCHAR(50),
                price_usd NUMERIC(20, 8),
                market_cap_usd NUMERIC(20, 2),
                volume_24h_usd NUMERIC(20, 2),
                change_percent_24h NUMERIC(10, 4),
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert data
        for asset in data:
            cur.execute("""
                INSERT INTO crypto_prices 
                (asset_id, symbol, name, price_usd, market_cap_usd, volume_24h_usd, change_percent_24h)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                asset.get('id'),
                asset.get('symbol'),
                asset.get('name'),
                float(asset.get('priceUsd', 0)),
                float(asset.get('marketCapUsd', 0)) if asset.get('marketCapUsd') else None,
                float(asset.get('volumeUsd24Hr', 0)) if asset.get('volumeUsd24Hr') else None,
                float(asset.get('changePercent24Hr', 0)) if asset.get('changePercent24Hr') else None
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
