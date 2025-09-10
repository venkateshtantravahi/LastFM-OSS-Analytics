"""Chart endpoints: global top artists/tracks/tags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import BaseExtractor


@dataclass
class ChartTopArtists(BaseExtractor):
    endpoint_name: str = "chart.getTopArtists"
    limit: int = 200

    def method_name(self) -> str:
        return "chart.getTopArtists"

    def build_params(self) -> Dict[str, Any]:
        return {"limit": self.limit}


@dataclass
class ChartTopTracks(BaseExtractor):
    endpoint_name: str = "chart.getTopTracks"
    limit: int = 200

    def method_name(self) -> str:
        return "chart.getTopTracks"

    def build_params(self) -> Dict[str, Any]:
        return {"limit": self.limit}


@dataclass
class ChartTopTags(BaseExtractor):
    endpoint_name: str = "chart.getTopTags"
    limit: int = 200

    def method_name(self) -> str:
        return "chart.getTopTags"

    def build_params(self) -> Dict[str, Any]:
        return {"limit": self.limit}
