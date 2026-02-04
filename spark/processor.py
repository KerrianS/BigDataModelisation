import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, current_timestamp
from pyspark.sql.types import DoubleType

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongo:27017/datalake.crypto_raw')
POSTGRES_URL = os.getenv('POSTGRES_URL', 'jdbc:postgresql://postgres:5432/bigdata_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'admin')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'admin')

def get_spark_session():
    return SparkSession.builder \
        .appName("MongoPostgresProcessor") \
        .config("spark.mongodb.input.uri", MONGO_URI) \
        .config("spark.mongodb.output.uri", MONGO_URI) \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1,org.postgresql:postgresql:42.6.0") \
        .getOrCreate()

def main():
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print("Reading from MongoDB...")
    
    # Read from MongoDB (Batch mode for simplicity in this architecture)
    # In a real streaming scenario with Mongo, you'd use a Change Stream or structured streaming.
    # Here we simulate a batch ETL job: Read All -> Transform -> Write to Postgres
    
    df = spark.read \
        .format("mongo") \
        .load()

    # Transform data
    # Select relevant columns and cast types
    processed_df = df.select(
        col("id").alias("asset_id"),
        col("symbol"),
        col("name"),
        col("priceUsd").cast(DoubleType()).alias("price_usd"),
        to_timestamp(col("ingestion_timestamp")).alias("timestamp")
    )

    print(f"Processing {processed_df.count()} records...")
    processed_df.show(5)

    # Write to Postgres
    print("Writing to PostgreSQL...")
    processed_df.write \
        .format("jdbc") \
        .option("url", POSTGRES_URL) \
        .option("dbtable", "crypto_prices") \
        .option("user", POSTGRES_USER) \
        .option("password", POSTGRES_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()
    
    print("Done.")

if __name__ == "__main__":
    main()
