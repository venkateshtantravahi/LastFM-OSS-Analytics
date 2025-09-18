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

    @task
    def user_top_artists(
        user: str = "rj",
        period: str = "1month",
        limit: int = 200,
        page: int = 3,
    ) -> str:
        return run_job(
            "user_top_artists",
            user=user,
            period=period,
            limit=limit,
            page=page,
        )

    @task
    def user_top_tracks(
        user: str = "rj",
        period: str = "1month",
        limit: int = 200,
        page: int = 3,
    ) -> str:
        return run_job(
            "user_top_tracks", user=user, period=period, limit=limit, page=page
        )

    @task
    def user_top_tags(user: str = "rj", limit: int = 100) -> str:
        return run_job("user_top_tags", user=user, limit=limit)

    # Parllel tasks no ordering dependency between them
    user_recent_tracks()
    user_top_artists()
    user_top_tracks()
    user_top_tags()
