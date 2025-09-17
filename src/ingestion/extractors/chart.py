"""Chart endpoints: global top artists/tracks/tags."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict

from src.ingestion.extractors.base import BaseExtractor, ExtractContext

LOG = logging.getLogger(__name__)


@dataclass(init=False)
class ChartTopArtists(BaseExtractor):
    endpoint_name: ClassVar[str] = "chart.getTopArtists"
    limit: int = 200

    def __init__(self, ctx: ExtractContext, limit: int = 200) -> None:
        super().__init__(ctx)
        self.limit = limit
        LOG.debug(
            "%s init: %s", self.__class__.__name__, {"limit": self.limit}
        )

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
        LOG.debug(
            "%s init: %s", self.__class__.__name__, {"limit": self.limit}
        )

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
        LOG.debug(
            "%s init: %s", self.__class__.__name__, {"limit": self.limit}
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"limit": self.limit}
