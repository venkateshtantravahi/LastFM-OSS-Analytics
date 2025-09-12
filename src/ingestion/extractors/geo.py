"""Geo endpoints: country-specific top artists/tracks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from .base import BaseExtractor, ExtractContext


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
        self.limit = limit

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
        self.limit = limit

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"country": self.country, "limit": self.limit}
