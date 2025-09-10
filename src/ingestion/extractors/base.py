"""Base extractor abstractions for Last.fm endpoints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from ..lastfm_client import LastFMClient
from ..storage import S3Storage


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
        payload = self.ctx.client.get(
            self.method_name(), **self.build_params()
        )
        key = self.output_key()
        self.ctx.storage.put_json(
            self.ctx.storage.settings.bucket, key, payload
        )
        return key
