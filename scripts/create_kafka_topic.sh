#!/bin/bash

echo "Creating Kafka topic: crypto-raw"

docker exec kafka kafka-topics --create \
  --topic crypto-raw \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

echo "Listing Kafka topics:"
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

echo "Kafka topic created successfully"
