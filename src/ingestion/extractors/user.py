"""User demo endpoints."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict

from .base import BaseExtractor, ExtractContext

LOG = logging.getLogger(__name__)


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
