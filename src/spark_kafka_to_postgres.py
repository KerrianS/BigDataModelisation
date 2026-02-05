from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType
import os

def create_spark_session():
    return SparkSession.builder \
        .appName("CryptoKafkaToPostgres") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1") \
        .getOrCreate()

def get_crypto_schema():
    return StructType([
        StructField("id", StringType(), True),
        StructField("symbol", StringType(), True),
        StructField("name", StringType(), True),
        StructField("current_price", DoubleType(), True),
        StructField("market_cap", DoubleType(), True),
        StructField("total_volume", DoubleType(), True),
        StructField("price_change_percentage_24h", DoubleType(), True),
        StructField("high_24h", DoubleType(), True),
        StructField("low_24h", DoubleType(), True),
        StructField("ath", DoubleType(), True),
        StructField("ath_change_percentage", DoubleType(), True),
        StructField("circulating_supply", DoubleType(), True),
        StructField("total_supply", DoubleType(), True),
        StructField("market_cap_rank", IntegerType(), True)
    ])

def process_kafka_stream():
    spark = create_spark_session()
    
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "crypto-raw") \
        .option("startingOffsets", "latest") \
        .load()
    
    value_df = kafka_df.selectExpr("CAST(value AS STRING)")
    
    parsed_df = value_df.select(
        from_json(col("value"), StructType([
            StructField("raw_data", ArrayType(get_crypto_schema()), True)
        ])).alias("data")
    )
    
    exploded_df = parsed_df.select(explode(col("data.raw_data")).alias("crypto"))
    
    final_df = exploded_df.select(
        col("crypto.id").alias("asset_id"),
        col("crypto.symbol"),
        col("crypto.name"),
        col("crypto.current_price").alias("price_usd"),
        col("crypto.market_cap").alias("market_cap_usd"),
        col("crypto.total_volume").alias("volume_24h_usd"),
        col("crypto.price_change_percentage_24h").alias("change_percent_24h"),
        col("crypto.high_24h"),
        col("crypto.low_24h"),
        col("crypto.ath"),
        col("crypto.ath_change_percentage"),
        col("crypto.circulating_supply"),
        col("crypto.total_supply"),
        col("crypto.market_cap_rank").alias("rank")
    )
    
    postgres_url = f"jdbc:postgresql://postgres:5432/{os.getenv('POSTGRES_DB', 'airflow')}"
    postgres_properties = {
        "user": os.getenv('POSTGRES_USER', 'airflow'),
        "password": os.getenv('POSTGRES_PASSWORD', 'airflow'),
        "driver": "org.postgresql.Driver"
    }
    
    query = final_df.writeStream \
        .foreachBatch(lambda batch_df, batch_id: 
            batch_df.write.jdbc(
                url=postgres_url,
                table="crypto_prices",
                mode="append",
                properties=postgres_properties
            )
        ) \
        .outputMode("append") \
        .start()
    
    query.awaitTermination()

if __name__ == "__main__":
    process_kafka_stream()
