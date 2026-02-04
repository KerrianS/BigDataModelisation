# Rapport de Projet Big Data

## 1. Problématique Métier

Dans un contexte de croissance exponentielle des données, les entreprises peinent à exploiter efficacement la masse d'informations hétérogènes à leur disposition. 
Les défis majeurs sont :
*   **Volumétrie** : Gérer de grandes quantités de données.
*   **Vitesse** : Ingérer et traiter les données en temps réel.
*   **Variété** : Intégrer des sources de données diverses.

Ce projet vise à mettre en place une **plateforme complète de traitement de données** capable de collecter, transformer et stocker des données financières réelles (Crypto-monnaies) pour l'aide à la décision.

## 2. Architecture Globale

La plateforme est conçue autour d'une architecture micro-services déployée via Docker, garantissant reproductibilité et isolation.

*   **Ingestion** : Apache Kafka
*   **Traitement** : Apache Spark (PySpark)
*   **Stockage** : PostgreSQL
*   **Orchestration** : Apache Airflow
*   **Infrastructure** : Docker & Docker Compose

## 3. Pipeline de Données

Le flux de données se déroule comme suit :

1.  **Ingestion (Producer)** : Un script Python interroge l'API **CoinCap** toutes les 10s et récupère les prix du Bitcoin, Ethereum, etc.
2.  **Tampon (Kafka)** : Les données JSON brutes sont envoyées dans le topic `crypto_stream`.
3.  **Traitement (Spark Streaming)** : 
    *   Lecture du flux Kafka.
    *   Validation du schéma.
    *   Extraction des champs : Symbol, Name, PriceUSD.
    *   Écriture continue dans PostgreSQL.
4.  **Stockage (PostgreSQL)** : Les données sont historisées dans la table `crypto_prices`.
5.  **Orchestration (Airflow)** : Surveille la disponibilité des services.

## 4. Modèle de Données

Les données brutes JSON de l'API CoinCap :
```json
{
    "id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "priceUsd": "23456.78",
    "timestamp": "2024-02-04T12:00:00"
}
```

Sont transformées en table `crypto_prices` :

| Colonne   | Type             | Description |
|-----------|------------------|-------------|
| id        | SERIAL (PK)      | Identifiant technique |
| symbol    | VARCHAR(20)      | Symbole (BTC, ETH...) |
| price_usd | DOUBLE PRECISION | Prix en Dollars |
| timestamp | TIMESTAMP        | Heure de la donnée |

## 5. Résultats et Conclusions

Ce projet a permis de démontrer la faisabilité d'une chaîne de traitement Big Data moderne. 
L'intégration de l'API CoinCap prouve la capacité de la plateforme à ingérer des flux externes en temps réel.
L'utilisation de **Kafka** assure la résilience, **Spark** la scalabilité et **PgAdmin** la restitution visuelle des données.
