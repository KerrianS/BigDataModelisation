# ETL Pipeline - Crypto Data Lake

[![Big Data Platform CI/CD](https://github.com/KerrianS/BigDataModelisation/actions/workflows/ci.yml/badge.svg)](https://github.com/KerrianS/BigDataModelisation/actions/workflows/ci.yml)

**Authors:** SALAÜN Kerrian & Raphaël DIMECK

## Project Overview

This project implements an ETL (Extract, Transform, Load) pipeline for cryptocurrency data ingestion using modern Big Data technologies. The system fetches real-time cryptocurrency market data from CoinGecko API and stores it in a MongoDB Data Lake for further analysis.

## Architecture

```mermaid
graph LR
    API[CoinGecko API] -->|REST| A[Airflow DAG]
    A -->|Insert| MONGO[(MongoDB Data Lake)]
    MONGO -->|Stream| P[Mongo-to-Kafka Producer]
    P -->|Publish| K[Kafka Topic]
    K -->|Consume| S[Spark Streaming]
    S -->|Transform & Write| PG[(PostgreSQL)]
    PG -->|Query| G[Grafana Dashboard]
    A -.->|Logs| L[Loki]
    L -.->|Visualize| G
```


- **Ingestion (Airflow)**: Python DAG that queries CoinGecko API every 3 minutes and stores raw data in MongoDB.
- **Data Lake (MongoDB)**: NoSQL database storing raw cryptocurrency data.
- **Streaming (Kafka)**: Message broker for real-time data streaming from MongoDB.
- **Processing (Spark)**: Structured Streaming job that consumes from Kafka, transforms data, and writes to PostgreSQL.
- **Data Warehouse (PostgreSQL)**: Relational database storing structured data for analysis.
- **Visualization (Grafana)**: Dashboards displaying crypto market metrics and trends.
- **Monitoring (Loki + Prometheus)**: Centralized logging and metrics collection.

> **Note**: Branch protection is configured on `main` to require all CI checks to pass before merging. See [docs/BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md) for setup instructions.

> **Security**: This project uses GitHub Secrets for CI/CD credentials. See [docs/GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md) for configuration instructions.

## Prerequisites

- Docker
- Docker Compose

## Installation and Launch

1. Clone this repository.
2. Check the `.env` file (default configurations are functional).
3. Launch the stack:

```bash
docker-compose up -d
```

## Project Structure

- `airflow/dags/`: Airflow DAGs (ingestion pipeline).
- `airflow/logs/`: Airflow logs.
- `src/`: Python utility scripts for testing and verification.
- `monitoring/`: Promtail and Grafana configuration.

## Service Access

- **Airflow UI**: http://localhost:8080 (airflow/airflow)
- **Grafana**: http://localhost:3000 (admin/admin)
- **MongoDB**: mongodb://admin:admin@localhost:27017/

## Environment Variables

All variables are defined in `.env`:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: PostgreSQL credentials (for Airflow metadata)
- `AIRFLOW_IMAGE_NAME`: Airflow Docker image
- `COINGECKO_API_URL`: CoinGecko API URL
- `CRYPTO_ASSETS`: List of cryptocurrencies to track
- `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`: MongoDB credentials
- `MONGO_DATABASE`: MongoDB database name
- `MONGO_COLLECTION`: MongoDB collection name

## Development

To modify the DAG, edit `airflow/dags/pipeline_dag.py` and restart the scheduler:
```bash
docker-compose restart airflow-scheduler
```

## MongoDB Data Access

### Via mongosh (command line):
```bash
docker exec bigdatamodelisation-mongo-1 mongosh --username admin --password admin --authenticationDatabase admin airflow_datalake
```

### Via MongoDB Compass (GUI):
- Connection URI: `mongodb://admin:admin@localhost:27017/`

### Via Python:
```python
from pymongo import MongoClient
client = MongoClient("mongodb://admin:admin@localhost:27017/")
db = client["airflow_datalake"]
collection = db["crypto_raw"]
```

## Utility Scripts

The `src/` directory contains helper scripts:

- `check_datalake.py`: Verify MongoDB data lake contents and display statistics
- `manual_ingestion.py`: Manually trigger data ingestion for testing
- `test_mongo.py`: Test MongoDB connection and insert test data
