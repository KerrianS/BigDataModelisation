from kafka import KafkaProducer
from pymongo import MongoClient
import json
import time
import os

def create_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
    )

def get_mongo_client():
    mongo_user = os.getenv('MONGO_INITDB_ROOT_USERNAME', 'admin')
    mongo_pass = os.getenv('MONGO_INITDB_ROOT_PASSWORD', 'admin')
    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@mongo:27017/"
    return MongoClient(mongo_uri)

def stream_mongodb_to_kafka():
    producer = create_kafka_producer()
    client = get_mongo_client()
    
    db = client["airflow_datalake"]
    collection = db["crypto_raw"]
    
    print("Starting MongoDB to Kafka streaming...")
    
    last_id = None
    
    while True:
        query = {"_id": {"$gt": last_id}} if last_id else {}
        
        documents = collection.find(query).sort("_id", 1)
        
        count = 0
        for doc in documents:
            producer.send('crypto-raw', value=doc)
            last_id = doc["_id"]
            count += 1
            print(f"Sent document {doc['_id']} to Kafka")
        
        if count > 0:
            producer.flush()
            print(f"Flushed {count} documents to Kafka")
        
        time.sleep(10)

if __name__ == "__main__":
    stream_mongodb_to_kafka()
