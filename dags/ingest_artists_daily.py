"""Ingest global Last.fm artists daily using Airflow TaskFlow API.


This DAG calls our programmatic entrypoint `run_job()` so we don't mutate
`sys.argv` inside tasks and we can unit-test tasks easily.
"""

from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.decorators import task

from src.ingestion.run_extract import run_job

DEFAULT_ARGS = {"owner": "lastfm", "retries": 1}

ARTIST_LIST = [
    "Jin",
    "Taylor Swift",
    "Tyler, The Creator",
    "Drake",
    "Playboi Carti",
    "Radiohead",
    "Kendrick Lamar",
    "Travi$ Scott",
]

with DAG(
    dag_id="ingest_artists_daily",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["lastfm", "artists"],
) as dag:

    @task
    def artist_top_tracks(
        artist: str = "Cher",
        autocorrect: int = 1,
        limit: int = 30,
        page: int = 3,
    ) -> str:
        return run_job(
            "artist_top_tracks",
            artist=artist,
            autocorrect=autocorrect,
            limit=limit,
            page=page,
        )

    @task
    def artist_top_tags(artist: str = "Cher", autocorrect: int = 1) -> str:
        return run_job(
            "artist_top_tags", artist=artist, autocorrect=autocorrect
        )

    @task
    def artist_top_albums(
        artist: str = "Cher",
        autocorrect: int = 1,
        limit: int = 20,
        page: int = 3,
    ) -> str:
        return run_job(
            "artist_top_albums",
            artist=artist,
            autocorrect=autocorrect,
            limit=limit,
            page=page,
        )

    @task
    def artist_get_info(
        artist: str = "Cher", lang: str = "en", autocorrect: int = 1
    ) -> str:
        return run_job(
            "artist_get_info",
            artist=artist,
            lang=lang,
            autocorrect=autocorrect,
        )

    @task
    def artist_get_similar(
        artist: str = "Cher", autocorrect: int = 1, limit: int = 20
    ) -> str:
        return run_job(
            "artist_get_similar",
            artist=artist,
            autocorrect=autocorrect,
            limit=limit,
        )

    # Parllel tasks no ordering dependency between them
    for artist in ARTIST_LIST:
        artist_top_tags(artist=artist)
        artist_top_albums(artist=artist)
        artist_get_info(artist=artist)
        artist_get_similar(artist=artist)
        artist_top_tracks(artist=artist)
