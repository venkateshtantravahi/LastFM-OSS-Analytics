"""Ingest global Last.fm charts daily using Airflow TaskFlow API.


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
    dag_id="ingest_chart_daily",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["lastfm", "ingestion", "charts"],
) as dag:

    @task
    def chart_top_artists(limit: int = 200) -> str:
        return run_job("chart_top_artists", limit=limit)

    @task
    def chart_top_tracks(limit: int = 200) -> str:
        return run_job("chart_top_tracks", limit=limit)

    @task
    def chart_top_tags(limit: int = 200) -> str:
        return run_job("chart_top_tags", limit=limit)

    # Parllel tasks no ordering dependency between them
    chart_top_artists()
    chart_top_tracks()
    chart_top_tags()
