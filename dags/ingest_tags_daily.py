"""Ingest global Last.fm tag related data daily using Airflow TaskFlow API.

This DAG calls our programmatic entrypoint `run_job()` so we dont mutate
`sys.argv` inside tasks and we can unit-test tasks easily.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from airflow import DAG
from airflow.decorators import task

from src.ingestion.run_extract import run_job

DEFAULT_ARGS = {"owner": "lastfm", "retries": 1}

with DAG(
    dag_id="ingest_tags_daily",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["lastfm", "tags"],
) as dag:

    @task
    def tags_get_info(
        tag: str = "disco",
        lang: Optional[str] = "en",
    ) -> str:
        return run_job("tags_get_info", tag=tag, lang=lang)

    @task
    def tags_top_artist(
        tag: str = "disco",
        limit: Optional[int] = 50,
        page: Optional[int] = 1,
    ) -> str:
        return run_job("tags_top_artist", tag=tag, limit=limit, page=page)

    @task
    def tags_top_tracks(
        tag: str = "disco", limit: Optional[int] = 50, page: Optional[int] = 1
    ) -> str:
        return run_job("tags_top_tracks", tag=tag, limit=limit, page=page)

    # Parllel tasks no ordering dependency between them
    tags_get_info()
    tags_top_artist()
    tags_top_tracks()
