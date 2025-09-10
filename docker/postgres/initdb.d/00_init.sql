-- RUNS AUTOMATICALLY ON FIRST CONTAINER START

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS curated;
CREATE TABLE IF NOT EXISTS raw.events (
    ingested_at timestamptz default now(),
    payload jsonb
);

CREATE DATABASE airflow_db;
CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;
