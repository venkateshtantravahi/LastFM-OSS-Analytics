-- Runs once on first container start.
-- Creates a separate analytics database and schemas/tables inside it.
-- Airflow metadata stays in the database named by POSTGRES_DB (from .env).

-- 1) Create the analytics database
CREATE DATABASE lastfm;

-- 2) Connect to it to create schemas/tables
\connect lastfm;

-- 3) App schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS curated;

-- 4) Minimal raw landing table for quick SQL inspection
CREATE TABLE IF NOT EXISTS raw.events (
    ingested_at timestamptz DEFAULT now(),
    payload      jsonb
);
