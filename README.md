# ETL Pipeline - Crypto Data Lake

[![Big Data Platform CI/CD](https://github.com/KerrianS/BigDataModelisation/actions/workflows/ci.yml/badge.svg)](https://github.com/KerrianS/BigDataModelisation/actions/workflows/ci.yml)

## Authors: SALAÜN Kerrian & Raphaël DIMECK

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
- **Grafana**: http://localhost:3000/d/crypto_dashboard/crypto-big-data-dashboard (admin/admin)
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

---

# Architecture & Operations (Technical Details)

This project implements a sophisticated **Data Lakehouse** architecture designed for reliability, scalability, and real-time insights. It bridges the gap between raw unstructured data (Data Lake) and high-performance structured analytics (Data Warehouse).

## 1. Deep Dive: The Data Journey

The pipeline is organized into four distinct logical layers, ensuring separation of concerns and system resilience.

### A. Ingestion Layer (The "Bronze" Stage)
*   **Mechanism:** An **Apache Airflow** DAG (`crypto_ingestion_pipeline`) acts as the primary orchestrator. Every 3 minutes, it triggers a Python function that performs a secure REST API call to **CoinGecko**.
*   **Data Capture:** It fetches the **Top 100 cryptocurrencies** by market cap, capturing a comprehensive JSON payload (prices, volumes, ATH, RSI indicators, etc.).
*   **Persistent Archiving:** The raw, unmodified JSON is timestamped and stored in **MongoDB**. This "Bronze" layer ensures that if our processing logic needs to change in the future, we can re-process historical data from its original source format.

### B. Brokerage & Decoupling Layer
*   **The Bridge:** A dedicated service (`mongo-to-kafka`) implements a **Change Data Capture (CDC)** pattern. It monitors the MongoDB collection for new document insertions using an incremental ID tracking strategy.
*   **Event Streaming:** New records are published to an **Apache Kafka** cluster (topic: `crypto-raw`). By introducing Kafka, we decouple the "Slow Ingestion" (API calls) from "Fast Processing" (Spark), allowing the system to handle spikes in data volume and providing a buffer for downstream consumers.

### C. Processing Layer (The "Silver" Stage)
*   **Compute Engine:** **Apache Spark** (via Structured Streaming) consumes the Kafka topic. Spark's distributed nature allows it to scale horizontally as data volume grows.
*   **Transformation Logic:**
    *   **Schema Enforcement:** Spark parses the semi-structured JSON using a predefined `StructType` schema. 
    *   **Normalization:** The nested `raw_data` array (containing 100 assets) is "exploded" into individual rows. 
    *   **Data Cleaning:** Data types are cast (e.g., String to Float for prices), and redundant fields are filtered out.
*   **The "Silver" Warehouse:** The resulting structured, clean data is streamed into **PostgreSQL** using a JDBC sink, creating a high-performance relational table (`crypto_prices`) ready for SQL queries.

### D. Visualization & Observability Layer
*   **Analytics:** **Grafana** is configured with a PostgreSQL datasource. It executes optimized SQL queries to render real-time candlestick charts, volatility heatmaps, and trend lines.
*   **Full-Stack Monitoring:** 
    *   **Logs:** System-wide logs are scraped by **Promtail**, indexed by **Loki**, and searchable directly within Grafana.
    *   **Metrics:** **Prometheus** tracks container health (CPU/RAM) and service uptime.

---

## 2. Technical Stack & Component Roles

| Component | Technology | Technical Responsibility | Why this choice? |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | **Airflow** | DAG scheduling, task retries, and API flow control. | Industry standard for complex, fault-tolerant workflows. |
| **NoSQL Lake** | **MongoDB** | Schema-less storage of original JSON documents. | Handles evolving API responses without breaking the pipeline. |
| **Streaming** | **Kafka** | High-throughput, distributed message brokerage. | Decouples services and provides a 7-day data retention buffer. |
| **Big Data Engine**| **Spark** | Distributed micro-batch processing & heavy transformations. | Fastest engine for structured streaming and complex ETL. |
| **Warehouse** | **Postgres** | Relational storage with indexing for analytical queries. | ACID compliance and excellent integration with BI tools. |
| **Observability** | **Grafana Stack** | Centralized dashboard for Data (SQL) and Infrastructure (Logs). | One-stop-shop for monitoring the entire ecosystem. |

---

## 3. System Resilience Features

*   **Internal Networking:** All components communicate within a dedicated **Docker bridge network**. Communication with databases is secured via internal DNS (e.g., `postgres:5432` instead of public IPs).
*   **Environment Isolation:** Credentials and API endpoints are never hardcoded; they are injected via a `.env` file, facilitating easy deployment across Dev, Staging, and Production.
*   **Auto-Healing:** Docker Compose is configured with `restart: unless-stopped` for critical ingestion services, ensuring the pipeline recovers automatically after container failures or system reboots.
*   **Storage Persistency:** **Docker Volumes** (`postgres_data`, `mongodb_data`, `grafana_data`) ensure that historical data and dashboard configurations survive container restarts and updates.