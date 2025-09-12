"""User demo endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from .base import BaseExtractor, ExtractContext


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
        self.limit = limit
        self.page = page

    def method_name(self) -> str:
        return self.endpoint_name

    def build_params(self) -> Dict[str, Any]:
        return {"user": self.user, "limit": self.limit, "page": self.page}
