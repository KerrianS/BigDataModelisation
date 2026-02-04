-- Create crypto_prices table
CREATE TABLE IF NOT EXISTS crypto_prices (
    id SERIAL PRIMARY KEY,
    asset_id VARCHAR(50),
    symbol VARCHAR(20),
    name VARCHAR(50),
    price_usd NUMERIC(20, 8),
    market_cap_usd NUMERIC(20, 2),
    volume_24h_usd NUMERIC(20, 2),
    change_percent_24h NUMERIC(10, 4),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON crypto_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_crypto_timestamp ON crypto_prices(ingestion_timestamp);
