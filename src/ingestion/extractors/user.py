"""User demo endpoints."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict, List

from .base import BaseExtractor, ExtractContext

LOG = logging.getLogger(__name__)

PERIOD_VALUES: List[str] = [
    "overall",
    "7day",
    "1month",
    "3month",
    "6month",
    "12month",
]


@dataclass(init=False)
class UserRecentTracks(BaseExtractor):
    user: str
    limit: int
    page: int
    endpoint_name: ClassVar[str] = "user.getRecentTracks"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        user: str = "rj",
        limit: int = 100,
        page: int = 1,
    ):
        super().__init__(ctx)
        self.user = user
        if not isinstance(self.user, str) or not self.user.strip():
            LOG.warning(
                "Empty/invalid user for %s; upstream may fail",
                self.__class__.__name__,
            )
        self.limit = limit
        self.page = page
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"limit": self.limit, "page": self.page, "user": self.user},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"user": self.user, "limit": self.limit, "page": self.page}


@dataclass(init=False)
class UserTopArtists(BaseExtractor):
    user: str
    period: str
    limit: int
    page: int
    endpoint_name: ClassVar[str] = "user.getTopArtists"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        user: str = "rj",
        period: str = "1month",
        limit: int = 100,
        page: int = 1,
    ):
        super().__init__(ctx)
        self.user = user
        if not isinstance(self.user, str) or not self.user.strip():
            LOG.warning(
                "Empty/invalid user for %s; upstream may fail",
                self.__class__.__name__,
            )
        self.period = period
        if (
            not isinstance(self.period, str)
            or self.period.strip() not in PERIOD_VALUES
        ):
            LOG.warning(
                "Invalid period value for %s; upstream may fail",
                self.__class__.__name__,
            )
        self.limit = limit
        self.page = page
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "limit": self.limit,
                "period": period,
                "page": self.page,
                "user": self.user,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "period": self.period,
            "limit": self.limit,
            "page": self.page,
        }


@dataclass(init=False)
class UserTopTracks(BaseExtractor):
    user: str
    period: str
    limit: int
    page: int
    endpoint_name: ClassVar[str] = "user.getTopTracks"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        user: str = "rj",
        period: str = "1month",
        limit: int = 100,
        page: int = 1,
    ):
        super().__init__(ctx)
        self.user = user
        if not isinstance(self.user, str) or not self.user.strip():
            LOG.warning(
                "Empty/invalid user for %s; upstream may fail",
                self.__class__.__name__,
            )
        self.period = period
        if (
            not isinstance(self.period, str)
            or self.period.strip() not in PERIOD_VALUES
        ):
            LOG.warning(
                "Invalid period value for %s; upstream may fail",
                self.__class__.__name__,
            )
        self.limit = limit
        self.page = page
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {
                "limit": self.limit,
                "period": period,
                "page": self.page,
                "user": self.user,
            },
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "period": self.period,
            "limit": self.limit,
            "page": self.page,
        }


@dataclass(init=False)
class UserTopTags(BaseExtractor):
    user: str
    limit: int
    endpoint_name: ClassVar[str] = "user.getTopTags"

    def __init__(
        self,
        ctx: ExtractContext,
        *,
        user: str = "rj",
        limit: int = 100,
    ):
        super().__init__(ctx)
        self.user = user
        if not isinstance(self.user, str) or not self.user.strip():
            LOG.warning(
                "Empty/invalid user for %s; upstream may fail",
                self.__class__.__name__,
            )
        self.limit = limit
        LOG.debug(
            "%s init: %s",
            self.__class__.__name__,
            {"limit": self.limit, "user": self.user},
        )

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"user": self.user, "limit": self.limit}
