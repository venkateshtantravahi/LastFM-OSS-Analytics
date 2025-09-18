"""Tags endpoints: global Tags info/tags/tracks."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict, Optional

from src.ingestion.extractors.base import BaseExtractor, ExtractContext

LOG = logging.getLogger(__name__)


@dataclass(init=False)
class TagGetInfo(BaseExtractor):
    tag: str
    lang: Optional[str]
    endpoint_name: ClassVar[str] = "tag.getInfo"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        tag: str = "disco",
        lang: Optional[str] = "en",
    ) -> None:
        super().__init__(ctx)
        self.tag = tag
        self.lang = lang
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"tag": self.tag, "lang": self.lang},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"tag": self.tag, "lang": self.lang}


@dataclass(init=False)
class TagGetTopArtist(BaseExtractor):
    tag: str
    limit: Optional[int]
    page: Optional[int]
    endpoint_name: ClassVar[str] = "tag.getTopArtists"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        tag: str = "disco",
        limit: Optional[int] = 50,
        page: Optional[int] = 1,
    ) -> None:
        super().__init__(ctx)
        self.tag = tag
        self.limit = limit
        self.page = page
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"tag": self.tag, "limit": self.limit, "page": self.page},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"tag": self.tag, "limit": self.limit, "page": self.page}


@dataclass(init=False)
class TagGetTopTracks(BaseExtractor):
    tag: str
    limit: Optional[int]
    page: Optional[int]
    endpoint_name: ClassVar[str] = "tag.getTopTracks"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        tag: str = "disco",
        limit: Optional[int] = 50,
        page: Optional[int] = 1,
    ) -> None:
        super().__init__(ctx)
        self.tag = tag
        self.limit = limit
        self.page = page
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"tag": self.tag, "limit": self.limit, "page": self.page},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"tag": self.tag, "limit": self.limit, "page": self.page}
