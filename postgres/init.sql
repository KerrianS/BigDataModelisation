CREATE TABLE IF NOT EXISTS crypto_prices (
    id SERIAL PRIMARY KEY,
    asset_id VARCHAR(100),
    symbol VARCHAR(20),
    name VARCHAR(100),
    price_usd NUMERIC(24, 8),
    market_cap_usd NUMERIC(24, 2),
    volume_24h_usd NUMERIC(24, 2),
    change_percent_24h NUMERIC(10, 4),
    high_24h NUMERIC(24, 8),
    low_24h NUMERIC(24, 8),
    ath NUMERIC(24, 8),
    ath_change_percentage NUMERIC(10, 4),
    circulating_supply NUMERIC(24, 2),
    total_supply NUMERIC(24, 2),
    rank INT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON crypto_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_crypto_timestamp ON crypto_prices(ingestion_timestamp);
CREATE INDEX IF NOT EXISTS idx_crypto_rank ON crypto_prices(rank);
