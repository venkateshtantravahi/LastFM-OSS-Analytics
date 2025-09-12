"""Chart endpoints: global top artists/tracks/tags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from .base import BaseExtractor, ExtractContext


@dataclass(init=False)
class ChartTopArtists(BaseExtractor):
    endpoint_name: ClassVar[str] = "chart.getTopArtists"
    limit: int = 200

    def __init__(self, ctx: ExtractContext, limit: int = 200) -> None:
        super().__init__(ctx)
        self.limit = limit

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"limit": self.limit}


@dataclass(init=False)
class ChartTopTracks(BaseExtractor):
    endpoint_name: ClassVar[str] = "chart.getTopTracks"
    limit: int = 200

    def __init__(self, ctx: ExtractContext, limit: int = 200) -> None:
        super().__init__(ctx)
        self.limit = limit

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"limit": self.limit}


@dataclass(init=False)
class ChartTopTags(BaseExtractor):
    endpoint_name: ClassVar[str] = "chart.getTopTags"
    limit: int = 200

    def __init__(self, ctx: ExtractContext, limit: int = 200) -> None:
        super().__init__(ctx)
        self.limit = limit

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"limit": self.limit}
