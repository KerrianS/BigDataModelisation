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
    'kafka_spark_pipeline',
    default_args=default_args,
    description='MongoDB to Kafka to PostgreSQL pipeline with Spark processing',
    schedule_interval=timedelta(minutes=5),
    catchup=False
)

def stream_mongo_to_kafka():
    """Stream latest MongoDB document to Kafka"""
    from kafka import KafkaProducer
    from pymongo import MongoClient
    import json
    
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
    )
    
    mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
    mongo_pass = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'admin')
    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@mongo:27017/"
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client["airflow_datalake"]
    collection = db["crypto_raw"]
    
    latest_doc = collection.find_one(sort=[("_id", -1)])
    
    if latest_doc:
        producer.send('crypto-raw', value=latest_doc)
        producer.flush()
        print(f"✅ Sent document {latest_doc['_id']} to Kafka topic 'crypto-raw'")
        print(f"📊 Document contains {latest_doc.get('data_points', 0)} crypto assets")
    else:
        print("⚠️ No documents found in MongoDB")
    
    client.close()

def process_kafka_to_postgres():
    """Consume from Kafka and write to PostgreSQL (Spark-style processing)"""
    from kafka import KafkaConsumer
    import psycopg2
    import json
    
    # Kafka consumer
    consumer = KafkaConsumer(
        'crypto-raw',
        bootstrap_servers=['kafka:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='spark-processor',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        consumer_timeout_ms=10000  # 10 seconds timeout
    )
    
    # PostgreSQL connection
    conn = psycopg2.connect(
        host='postgres',
        database=os.getenv('POSTGRES_DB', 'airflow'),
        user=os.getenv('POSTGRES_USER', 'airflow'),
        password=os.getenv('POSTGRES_PASSWORD', 'airflow')
    )
    cur = conn.cursor()
    
    total_processed = 0
    
    print("🔄 Starting Kafka consumer...")
    for message in consumer:
        doc = message.value
        raw_data = doc.get('raw_data', [])
        
        print(f"📥 Processing message from Kafka: {len(raw_data)} assets")
        
        for asset in raw_data:
            try:
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
                total_processed += 1
            except Exception as e:
                print(f"❌ Error processing asset {asset.get('id')}: {e}")
                continue
        
        conn.commit()
        print(f"✅ Committed {len(raw_data)} records to PostgreSQL")
    
    cur.close()
    conn.close()
    consumer.close()
    
    print(f"🎉 Pipeline complete! Processed {total_processed} total crypto assets")

# Task 1: Stream from MongoDB to Kafka
stream_task = PythonOperator(
    task_id='stream_mongo_to_kafka',
    python_callable=stream_mongo_to_kafka,
    dag=dag,
)

# Task 2: Process Kafka messages and write to PostgreSQL
process_task = PythonOperator(
    task_id='process_kafka_to_postgres',
    python_callable=process_kafka_to_postgres,
    dag=dag,
)

# Pipeline flow: MongoDB → Kafka → PostgreSQL
stream_task >> process_task
