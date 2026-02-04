CREATE TABLE IF NOT EXISTS crypto_prices (
    id SERIAL PRIMARY KEY,
    asset_id VARCHAR(50),
    symbol VARCHAR(20),
    name VARCHAR(50),
    price_usd DOUBLE PRECISION,
    timestamp TIMESTAMP
);
