"""Geo endpoints: country-specific top artists/tracks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import BaseExtractor


@dataclass
class GeoTopArtists(BaseExtractor):
    country: str = "united states"
    limit: int = 200
    endpoint_name = "geo.getTopArtists"

    def method_name(self) -> str:
        return "geo.getTopArtists"

    def build_params(self) -> Dict[str, Any]:
        return {"country": self.country, "limit": self.limit}


@dataclass
class GeoTopTracks(BaseExtractor):
    country: str = "united states"
    limit: int = 200
    endpoint_name = "geo.getTopTracks"

    def method_name(self) -> str:
        return "geo.getTopTracks"

    def build_params(self) -> Dict[str, Any]:
        return {"country": self.country, "limit": self.limit}
