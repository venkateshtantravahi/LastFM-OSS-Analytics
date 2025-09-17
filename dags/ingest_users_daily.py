"""Ingest global Last.fm users daily using Airflow TaskFlow API.


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
    dag_id="ingest_users_daily",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["lastfm", "users"],
) as dag:

    @task
    def user_recent_tracks(
        user: str = "rj", limit: int = 200, page: int = 3
    ) -> str:
        return run_job("user_recent_tracks", user=user, limit=limit, page=page)

    # Parllel tasks no ordering dependency between them
    user_recent_tracks()
