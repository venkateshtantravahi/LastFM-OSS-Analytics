"""Base extractor abstractions for Last.fm endpoints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
import logging
from typing import Any, Dict, Optional

from src.ingestion.lastfm_client import LastFMClient
from src.ingestion.storage import S3Storage

LOG = logging.getLogger(__name__)


@dataclass
class ExtractContext:
    """Shared context for extractors."""

    client: LastFMClient
    storage: S3Storage


class BaseExtractor(ABC):
    """Common extractor interface for all endpoints."""

    endpoint_name: str  # used in bucket partitioning

    def __init__(self, ctx: ExtractContext) -> None:
        self.ctx = ctx

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if "limit" in params:
            try:
                val = int(params["limit"])
                params["limit"] = max(1, min(200, val))
            except Exception:
                LOG.warning(
                    "Invalid 'limit' value (%r) for %s passing through",
                    params["limit"],
                    self.__class__.__name__,
                )
        if "page" in params:
            try:
                val = int(params["page"])
                params["page"] = max(1, val)
            except Exception:
                LOG.warning(
                    "Invalid 'page' value (%r) for %s passing through",
                    params["page"],
                    self.__class__.__name__,
                )
        return params

    def _resolve_bucket(self) -> str:
        s = self.ctx.storage.settings
        return getattr(s, "bucket_raw", getattr(s, "bucket", None))

    @abstractmethod
    def build_params(self) -> Dict[str, Any]:
        """
        Return the method-specific params (without api_key/format).
        :return:
        """

    @abstractmethod
    def method_name(self) -> str:
        """
        Return the Last.fm method name.
        :return:
        """

    def output_key(self, d: Optional[date] = None) -> str:
        return self.ctx.storage.partition_key(self.endpoint_name, d)

    def run(self) -> str:
        """
        Execute the extractor, write payload to bucket and return
        object key
        :return:
        """
        method = self.method_name()
        raw_params = self.build_params()
        params = self._sanitize_params(raw_params)

        LOG.info(
            "Exctractor start: %s method=%s params=%s",
            self.__class__.__name__,
            method,
            params,
        )

        try:
            payload = self.ctx.client.get(method, **params)
            key = self.output_key()
            bucket = self._resolve_bucket()
            if not bucket:
                from src.ingestion.exception import ConfigError

                raise ConfigError(
                    "No S3 bucket configured (expected bucket_raw)"
                )
            self.ctx.storage.put_json(bucket, key, payload)

            LOG.info(
                "Extractor success: %s -> s3://%s/%s",
                self.__class__.__name__,
                bucket,
                key,
            )
            return key
        except Exception as e:
            from src.ingestion.exception import (
                AuthError,
                ExtractorError,
                RateLimitError,
                StorageError,
                UpstreamError,
            )

            if isinstance(
                e, (AuthError, RateLimitError, UpstreamError, StorageError)
            ):
                LOG.error(
                    "Extractor failed (%s): %s params=%s",
                    type(e).__name__,
                    method,
                    params,
                    exc_info=True,
                )
                raise
            LOG.error(
                "Extractor unexpected error: %s params=%s",
                method,
                params,
                exc_info=True,
            )
            raise ExtractorError(str(e))
