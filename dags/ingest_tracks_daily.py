"""Ingest global Last.fm tracks daily using Airflow TaskFlow API.


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
    dag_id="ingest_tracks_daily",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["lastfm", "tracks"],
) as dag:

    @task
    def tracks_get_info(
        track: str = "believe", artist: str = "cher", autocorrect: int = 1
    ) -> str:
        return run_job(
            "tracks_get_info",
            artist=artist,
            track=track,
            autocorrect=autocorrect,
        )

    @task
    def tracks_get_similar(
        track: str = "believe",
        artist: str = "cher",
        autocorrect: int = 1,
        limit: int = 50,
    ) -> str:
        return run_job(
            "tracks_get_similar",
            track=track,
            artist=artist,
            limit=limit,
            autocorrect=autocorrect,
        )

    @task
    def tracks_get_top_tags(
        track: str = "believe", artist: str = "cher", autocorrect: int = 1
    ) -> str:
        return run_job(
            "tracks_get_top_tags",
            artist=artist,
            track=track,
            autocorrect=autocorrect,
        )

    # Parllel tasks no ordering dependency between them
    tracks_get_info()
    tracks_get_similar()
    tracks_get_top_tags()
