"""Ingest global Last.fm top artists daily using Airflow TaskFlow API.


This DAG calls our programmatic entrypoint `run_job()` so we don't mutate
`sys.argv` inside tasks and we can unit-test tasks easily.
"""

from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.decorators import task

from src.ingestion.run_extract import run_job

DEFAULT_ARGS = {"owner": "lastfm", "retries": 1}

with DAG(
    dag_id="ingest_geo_daily",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["lastfm", "geo"],
) as dag:

    @task
    def geo_top_artists(
        country: str = "united states", limit: int = 200
    ) -> str:
        return run_job("geo_top_artists", country=country, limit=limit)

    @task
    def geo_top_tracks(
        country: str = "united states", limit: int = 200
    ) -> str:
        return run_job("geo_top_tracks", country=country, limit=limit)

    # Parllel tasks no ordering dependency between them
    geo_top_artists()
    geo_top_tracks()
