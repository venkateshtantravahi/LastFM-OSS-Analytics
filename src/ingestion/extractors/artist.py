"""Artists endpoints: global artists info/tags/tracks."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict

from src.ingestion.extractors.base import BaseExtractor, ExtractContext

LOG = logging.getLogger(__name__)


@dataclass(init=False)
class ArtistGetInfo(BaseExtractor):
    artist: str
    lang: str
    autocorrect: int
    endpoint_name: ClassVar[str] = "artist.getInfo"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "Cher",
        lang: str = "en",
        autocorrect: int = 1,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.lang = lang
        self.autocorrect = autocorrect
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "artist": self.artist,
                "lang": self.lang,
                "autocorrect": self.autocorrect,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "artist": self.artist,
            "lang": self.lang,
            "autocorrect": self.autocorrect,
        }


@dataclass(init=False)
class ArtistTopTags(BaseExtractor):
    artist: str
    autocorrect: int
    endpoint_name: ClassVar[str] = "artist.getTopTags"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "Cher",
        autocorrect: int = 1,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.autocorrect = autocorrect
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"artist": self.artist, "autocorrect": self.autocorrect},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"artist": self.artist, "autocorrect": self.autocorrect}


@dataclass(init=False)
class ArtistTopTracks(BaseExtractor):
    artist: str
    autocorrect: int
    page: int
    limit: int
    endpoint_name: ClassVar[str] = "artist.getTopTracks"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "Cher",
        autocorrect: int = 1,
        page: int = 2,
        limit: int = 10,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.autocorrect = autocorrect
        self.page = page
        self.limit = limit
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "artist": self.artist,
                "autocorrect": self.autocorrect,
                "page": self.page,
                "limit": self.limit,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "artist": self.artist,
            "autocorrect": self.autocorrect,
            "page": self.page,
            "limit": self.limit,
        }


@dataclass(init=False)
class ArtistTopAlbums(BaseExtractor):
    artist: str
    autocorrect: int
    page: int
    limit: int
    endpoint_name: ClassVar[str] = "artist.getTopAlbums"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "Cher",
        autocorrect: int = 1,
        page: int = 2,
        limit: int = 10,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.autocorrect = autocorrect
        self.page = page
        self.limit = limit
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "artist": self.artist,
                "autocorrect": self.autocorrect,
                "page": self.page,
                "limit": self.limit,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "artist": self.artist,
            "autocorrect": self.autocorrect,
            "page": self.page,
            "limit": self.limit,
        }


@dataclass(init=False)
class ArtistGetSimilar(BaseExtractor):
    artist: str
    autocorrect: int
    limit: int
    endpoint_name: ClassVar[str] = "artist.getTopAlbums"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        artist: str = "Cher",
        autocorrect: int = 1,
        limit: int = 10,
    ) -> None:
        super().__init__(ctx)
        self.artist = artist
        self.autocorrect = autocorrect
        self.limit = limit
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "artist": self.artist,
                "autocorrect": self.autocorrect,
                "limit": self.limit,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "artist": self.artist,
            "autocorrect": self.autocorrect,
            "limit": self.limit,
        }
