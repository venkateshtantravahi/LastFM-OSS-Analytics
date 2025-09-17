"""Geo endpoints: country-specific top artists/tracks."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict

from .base import BaseExtractor, ExtractContext

LOG = logging.getLogger(__name__)


@dataclass(init=False)
class GeoTopArtists(BaseExtractor):
    country: str
    limit: int
    endpoint_name: ClassVar[str] = "geo.getTopArtists"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        country: str = "united states",
        limit: int = 200,
    ) -> None:
        super().__init__(ctx)
        self.country = country
        if not isinstance(self.country, str) or not self.country.strip():
            LOG.warning(
                "Empty/invalid country for %s upstream may fail",
                self.__class__.__name__,
            )
        self.limit = limit
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"limit": self.limit, "country": self.country},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"country": self.country, "limit": self.limit}


@dataclass(init=False)
class GeoTopTracks(BaseExtractor):
    country: str
    limit: int
    endpoint_name: ClassVar[str] = "geo.getTopTracks"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        country: str = "united states",
        limit: int = 200,
    ) -> None:
        super().__init__(ctx)
        self.country = country
        if not isinstance(self.country, str) or not self.country.strip():
            LOG.warning(
                "Empty/invalid country for %s upstream may fail",
                self.__class__.__name__,
            )
        self.limit = limit
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"limit": self.limit, "country": self.country},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"country": self.country, "limit": self.limit}
