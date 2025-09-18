"""CLI entrypoint to run a single extractor and write to S3.


Example usage:
python -m src.ingestion.run_extract --job chart_top_artists
python -m src.ingestion.run_extract --job geo_top_tracks --country "india"
python -m src.ingestion.run_extract --job user_recent_tracks --user "rj"
"""

from __future__ import annotations

import argparse
import logging
import os
from types import SimpleNamespace
from typing import Type
import uuid

from dotenv import load_dotenv

from src.ingestion.config import AppSettings
from src.ingestion.exception import RateLimitError, UpstreamError
from src.ingestion.extractors.artist import (
    ArtistGetInfo,
    ArtistGetSimilar,
    ArtistTopAlbums,
    ArtistTopTags,
    ArtistTopTracks,
)
from src.ingestion.extractors.base import BaseExtractor, ExtractContext
from src.ingestion.extractors.chart import (
    ChartTopArtists,
    ChartTopTags,
    ChartTopTracks,
)
from src.ingestion.extractors.geo import GeoTopArtists, GeoTopTracks
from src.ingestion.extractors.tags import (
    TagGetInfo,
    TagGetTopArtist,
    TagGetTopTracks,
)
from src.ingestion.extractors.tracks import (
    TracksGetInfo,
    TracksGetSimilar,
    TracksGetTopTags,
)
from src.ingestion.extractors.user import (
    PERIOD_VALUES,
    UserRecentTracks,
    UserTopArtists,
    UserTopTags,
    UserTopTracks,
)
from src.ingestion.lastfm_client import LastFMClient
from src.ingestion.secrets import (
    EnvSecretProvider as _EnvSecretProvider,
    VaultKV2Provider as _VaultKv2Provider,
)
from src.ingestion.storage import S3Storage

LOG = logging.getLogger(__name__)

load_dotenv(
    dotenv_path="/Users/venkateshtantravahi/"
    + "PycharmProjects/LastFM-OSS-Analytics/infra/.env"
)

EXTRACTOR_REGISTRY = {
    "chart_top_artists": ChartTopArtists,
    "chart_top_tracks": ChartTopTracks,
    "chart_top_tags": ChartTopTags,
    "geo_top_artists": GeoTopArtists,
    "geo_top_tracks": GeoTopTracks,
    "user_recent_tracks": UserRecentTracks,
    "user_top_artists": UserTopArtists,
    "user_top_tags": UserTopTags,
    "user_top_tracks": UserTopTracks,
    "artist_top_tracks": ArtistTopTracks,
    "artist_top_tags": ArtistTopTags,
    "artist_top_albums": ArtistTopAlbums,
    "artist_get_info": ArtistGetInfo,
    "artist_get_similar": ArtistGetSimilar,
    "tracks_get_info": TracksGetInfo,
    "tracks_get_similar": TracksGetSimilar,
    "tracks_get_top_tags": TracksGetTopTags,
    "tags_get_info": TagGetInfo,
    "tags_top_artist": TagGetTopArtist,
    "tags_top_tracks": TagGetTopTracks,
}

EnvSecretsProvider = _EnvSecretProvider
VaultKV2Provider = _VaultKv2Provider


def summarize_settings(s: AppSettings) -> dict:
    return {
        "log_level": getattr(s, "log_level", "INFO"),
        "s3_endpoint": getattr(s.s3, "endpoint_url", None),
        "s3_region": getattr(s.s3, "region_name", None),
        "s3_bucket_raw": getattr(s.s3, "bucket_raw", None),
        "vault_addr": getattr(
            s,
            "vault_addr",
            getattr(getattr(s, "vault", object()), "addr", None),
        ),
    }


def _resolve_api_key(settings: AppSettings) -> str:
    # using flat attr
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_DEV_ROOT_TOKEN_ID")
    kv_mount = os.getenv("VAULT_KV_MOUNT")
    path = os.getenv("VAULT_SECRET_PATH")
    key = os.getenv("VAULT_SECRET_KEY")

    vault = VaultKV2Provider(addr=addr, token=token, kv_mount=kv_mount)
    val = vault.get(path, key)
    return val


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
    if cls in (UserTopTracks, UserTopArtists):
        return cls(
            ctx,
            user=args.user,
            period=args.period,
            limit=args.limit,
            page=args.page,
        )
    if cls is UserTopTags:
        return cls(ctx, user=args.user, limit=args.limit)
    if cls in (GeoTopTracks, GeoTopArtists):
        return cls(ctx, country=args.country, limit=args.limit)
    if cls is ArtistGetInfo:
        return cls(
            ctx,
            artist=args.artist,
            lang=args.lang,
            autocorrect=args.autocorrect,
        )
    if cls is ArtistTopTags:
        return cls(ctx, artist=args.artist, autocorrect=args.autocorrect)
    if cls in (ArtistTopTracks, ArtistTopAlbums):
        return cls(
            ctx,
            artist=args.artist,
            autocorrect=args.autocorrect,
            page=args.page,
            limit=args.limit,
        )
    if cls is ArtistGetSimilar:
        return cls(
            ctx,
            artist=args.artist,
            autocorrect=args.autocorrect,
            limit=args.limit,
        )
    if cls in (TracksGetInfo, TracksGetTopTags):
        return cls(
            ctx,
            artist=args.artist,
            track=args.track,
            autocorrect=args.autocorrect,
        )
    if cls is TracksGetSimilar:
        return cls(
            ctx,
            artist=args.artist,
            limit=args.limit,
            track=args.track,
            autocorrect=args.autocorrect,
        )
    if cls is TagGetInfo:
        return cls(ctx, tag=args.tag, lang=args.lang)
    if cls in (TagGetTopArtist, TagGetTopTracks):
        return cls(ctx, tag=args.tag, limit=args.limit, page=args.page)
    return cls(ctx, limit=args.limit)


def run_job(
    job: str,
    *,
    limit: int = 200,
    tag: str = "disco",
    country: str = "united states",
    user: str = "rj",
    artist: str = "Cher",
    track: str = "believe",
    lang: str = "en",
    autocorrect: int = 1,
    period: str = "1month",
    page: int = 1,
) -> str:
    """Run an extractor programmatically and return the S3 object key.


    This is the preferred entrypoint for Airflow TaskFlow tasks.
    """
    settings = AppSettings()
    limit = max(1, min(200, int(limit))) if isinstance(limit, int) else 200
    page = max(1, int(page)) if isinstance(page, int) else 1
    autocorrect = (
        max(1, int(autocorrect)) if isinstance(autocorrect, int) else 1
    )
    args = SimpleNamespace(
        limit=limit,
        tag=tag,
        country=country,
        artist=artist,
        period=period,
        track=track,
        user=user,
        page=page,
        autocorrect=autocorrect,
        lang=lang,
    )
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
    parser.add_argument("--period", type=str, default="7day")
    parser.add_argument("--autocorrect", type=int, default=1)
    parser.add_argument("--lang", type=str, default="en")
    parser.add_argument("--artist", type=str, default="Cher")
    parser.add_argument("--track", type=str, default="believe")
    parser.add_argument("--tag", type=str, default="disco")

    args = parser.parse_args()

    if hasattr(settings, "configure_logging"):
        settings.configure_logging()
    else:
        logging.basicConfig(
            level=getattr(
                logging,
                str(getattr(settings, "log_level", "INFO")).upper(),
                logging.INFO,
            ),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )

    correlation_id = os.environ.get("CORRELATION_ID", uuid.uuid4().hex)
    os.environ["CORRELATION_ID"] = correlation_id
    LOG.info(
        "Job start correlation_id=%s settings=%s",
        correlation_id,
        summarize_settings(settings),
    )

    # CLI Validation
    if args.job.startswith("user_") and not args.user:
        LOG.error("Missing --user for job=%s", args.job)
        raise SystemExit(2)
    if args.limit is not None and (args.limit < 1 or args.limit > 200):
        LOG.warning("Clamping --limit=%s to [1,200]", args.limit)
        args.limit = max(1, min(200, args.limit))
    if args.page is not None and args.page < 1:
        LOG.warning("Clamping --page=%s to >=1", args.page)
        args.page = max(1, args.page)
    if args.period is not None and args.period not in PERIOD_VALUES:
        LOG.warning("Clamping --period=%s to 7day", args.period)
        args.period = "7day"
    if args.autocorrect is not None and args.autocorrect not in [0, 1]:
        LOG.warning("Clamping --autocorrect=%s to 0", args.autocorrect)
        args.autocorrect = 0

    try:
        exctractor = build_extractor(settings, args.job, args)
        key = exctractor.run()
        LOG.info("Job success correlation_id=%s key=%s", correlation_id, key)
        LOG.info(
            "Wrote object to s3://%s/%s",
            getattr(settings.s3, "bucket_raw", "<unknown>"),
            key,
        )
    except (RateLimitError, UpstreamError) as e:
        LOG.warning(
            "Job recoverable failure correlation_id=%s: %s",
            correlation_id,
            e,
            exc_info=True,
        )
        raise
    except Exception as e:
        LOG.error(
            "Job failed correlation_id=%s: %s",
            correlation_id,
            e,
            exc_info=True,
        )
        raise


if __name__ == "__main__":
    main()
