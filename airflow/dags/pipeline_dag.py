from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import pymongo
import psycopg2

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
    'datalake_pipeline',
    default_args=default_args,
    description='Pipeline orchestration: API -> Mongo -> Spark -> Postgres',
    schedule_interval=timedelta(minutes=10),
    catchup=False
)

def check_mongo_connection():
    try:
        # In a real Airflow setup, use a Connection defined in UI
        # For this demo, we use Env vars or default docker DNS
        client = pymongo.MongoClient("mongodb://admin:admin@mongo:27017/")
        db = client.datalake
        print("Connected to MongoDB")
        print("Collections:", db.list_collection_names())
        client.close()
    except Exception as e:
        print(f"Mongo connection failed: {e}")
        raise e

def check_postgres_connection():
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="bigdata_db",
            user="admin",
            password="admin"
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        print("Postgres is reachable.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Postgres connection failed: {e}")
        raise e

# Define tasks
check_mongo_task = PythonOperator(
    task_id='check_mongo_availability',
    python_callable=check_mongo_connection,
    dag=dag,
)

check_postgres_task = PythonOperator(
    task_id='check_postgres_availability',
    python_callable=check_postgres_connection,
    dag=dag,
)

check_mongo_task >> check_postgres_task
