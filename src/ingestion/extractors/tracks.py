"""Tracks endpoints: global Tracks info/tags/tracks."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict

from src.ingestion.extractors.base import BaseExtractor, ExtractContext

LOG = logging.getLogger(__name__)


@dataclass(init=False)
class TracksGetInfo(BaseExtractor):
    track: str
    artist: str
    autocorrect: int
    endpoint_name: ClassVar[str] = "track.getInfo"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "cher",
        track: str = "believe",
        autocorrect: int = 1,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.track = track
        self.autocorrect = autocorrect
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "artist": self.artist,
                "track": self.track,
                "autocorrect": self.autocorrect,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "artist": self.artist,
            "track": self.track,
            "autocorrect": self.autocorrect,
        }


@dataclass(init=False)
class TracksGetSimilar(BaseExtractor):
    track: str
    artist: str
    autocorrect: int
    limit: int
    endpoint_name: ClassVar[str] = "track.getSimilar"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "cher",
        track: str = "believe",
        autocorrect: int = 1,
        limit: int = 50,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.track = track
        self.autocorrect = autocorrect
        self.limit = limit
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "artist": self.artist,
                "track": self.track,
                "limit": self.limit,
                "autocorrect": self.autocorrect,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "artist": self.artist,
            "limit": self.limit,
            "track": self.track,
            "autocorrect": self.autocorrect,
        }


@dataclass(init=False)
class TracksGetTopTags(BaseExtractor):
    track: str
    artist: str
    autocorrect: int
    endpoint_name: ClassVar[str] = "track.getTopTags"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "cher",
        track: str = "believe",
        autocorrect: int = 1,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.track = track
        self.autocorrect = autocorrect
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "artist": self.artist,
                "track": self.track,
                "autocorrect": self.autocorrect,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "artist": self.artist,
            "track": self.track,
            "autocorrect": self.autocorrect,
        }
