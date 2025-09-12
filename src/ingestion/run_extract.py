"""CLI entrypoint to run a single extractor and write to S3.


Example usage:
python -m src.ingestion.run_extract --job chart_top_artists
python -m src.ingestion.run_extract --job geo_top_tracks --country "india"
python -m src.ingestion.run_extract --job user_recent_tracks --user "rj"
"""

from __future__ import annotations

import argparse
import logging
from types import SimpleNamespace
from typing import Type

from src.ingestion.config import AppSettings
from src.ingestion.extractors.base import BaseExtractor, ExtractContext
from src.ingestion.extractors.chart import (
    ChartTopArtists,
    ChartTopTags,
    ChartTopTracks,
)
from src.ingestion.extractors.geo import GeoTopArtists, GeoTopTracks
from src.ingestion.extractors.user import UserRecentTracks
from src.ingestion.lastfm_client import LastFMClient
from src.ingestion.secrets import (
    EnvSecretProvider as _EnvSecretProvider,
    VaultKV2Provider as _VaultKv2Provider,
    resolve_lastfm_api_key,
)
from src.ingestion.storage import S3Storage

EXTRACTOR_REGISTRY = {
    "chart_top_artists": ChartTopArtists,
    "chart_top_tracks": ChartTopTracks,
    "chart_top_tags": ChartTopTags,
    "geo_top_artists": GeoTopArtists,
    "geo_top_tracks": GeoTopTracks,
    "user_recent_tracks": UserRecentTracks,
}

EnvSecretsProvider = _EnvSecretProvider
VaultKV2Provider = _VaultKv2Provider


def _resolve_api_key(settings: AppSettings) -> str:
    env_provider = EnvSecretsProvider(prefix="")
    key = env_provider.get("lastfm", "LASTFM_API_KEY")
    if not key:
        vault = VaultKV2Provider(
            addr=settings.vault_addr,
            token=settings.vault.token,
            kv_mount=settings.vault.kv_mount,
        )
        key = resolve_lastfm_api_key(vault)
    return key


def build_extractor(
    settings: AppSettings, job: str, args: argparse.Namespace
) -> BaseExtractor:
    """Construct an extractor from registry with resolved secrets.


    Parameters
    ----------
    settings: AppSettings
    Loaded configuration.
    job: str
    Registry key, e.g. "chart_top_artists".
    args: SimpleNamespace
    Holds optional parameters like limit/country/user/page.
    """
    cls: Type[BaseExtractor] = EXTRACTOR_REGISTRY[job]

    key = _resolve_api_key(settings)
    client = LastFMClient(api_key=key)
    storage = S3Storage(settings.s3)
    ctx = ExtractContext(client=client, storage=storage)

    if cls is UserRecentTracks:
        return cls(ctx, user=args.user, limit=args.limit, page=args.page)
    if cls in (GeoTopTracks, GeoTopArtists):
        return cls(ctx, country=args.country, limit=args.limit)
    return cls(ctx, limit=args.limit)


def run_job(
    job: str,
    *,
    limit: int = 200,
    country: str = "united states",
    user: str = "rj",
    page: int = 1,
) -> str:
    """Run an extractor programmatically and return the S3 object key.


    This is the preferred entrypoint for Airflow TaskFlow tasks.
    """
    settings = AppSettings()
    args = SimpleNamespace(limit=limit, country=country, user=user, page=page)
    extractor = build_extractor(settings, job, args)
    return extractor.run()


def main() -> None:
    settings = AppSettings()

    parser = argparse.ArgumentParser(description="Run a LastFM extractor job.")
    parser.add_argument(
        "--job", choices=EXTRACTOR_REGISTRY.keys(), required=True
    )
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--country", type=str, default="united states")
    parser.add_argument("--user", type=str, default="rj")
    parser.add_argument("--page", type=int, default=1)

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO)
    )
    logging.info("Starting job: %s", args.job)

    # ns = SimpleNamespace(**vars(args))
    extractor = build_extractor(settings, args.job, args)
    key = extractor.run()
    logging.info("Wrote object to bucket://%s/%s", settings.s3.bucket_raw, key)


if __name__ == "__main__":
    main()
