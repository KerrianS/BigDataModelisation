from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
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
    'mongo_to_postgres_direct',
    default_args=default_args,
    description='Direct MongoDB to PostgreSQL pipeline',
    schedule_interval=timedelta(minutes=5),
    catchup=False
)

def transfer_data():
    from pymongo import MongoClient
    import psycopg2
    
    mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
    mongo_pass = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'admin')
    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@mongo:27017/"
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client["airflow_datalake"]
    collection = db["crypto_raw"]
    
    latest_doc = collection.find_one(sort=[("_id", -1)])
    
    if not latest_doc:
        print("No documents found in MongoDB")
        return
    
    raw_data = latest_doc.get('raw_data', [])
    print(f"Found {len(raw_data)} crypto assets to insert")
    
    conn = psycopg2.connect(
        host='postgres',
        database=os.getenv('POSTGRES_DB', 'airflow'),
        user=os.getenv('POSTGRES_USER', 'airflow'),
        password=os.getenv('POSTGRES_PASSWORD', 'airflow')
    )
    cur = conn.cursor()
    
    for asset in raw_data:
        cur.execute("""
            INSERT INTO crypto_prices 
            (asset_id, symbol, name, price_usd, market_cap_usd, volume_24h_usd, 
             change_percent_24h, high_24h, low_24h, ath, ath_change_percentage, 
             circulating_supply, total_supply, rank)
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
    print(f"Successfully inserted {len(raw_data)} records into PostgreSQL")
    
    cur.close()
    conn.close()
    client.close()

transfer_task = PythonOperator(
    task_id='transfer_mongo_to_postgres',
    python_callable=transfer_data,
    dag=dag,
)

transfer_task
