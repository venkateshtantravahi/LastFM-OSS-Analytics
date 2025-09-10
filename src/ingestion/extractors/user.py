"""User demo endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import BaseExtractor


@dataclass
class UserRecentTracks(BaseExtractor):
    user: str = "rj"
    limit: int = 200
    page: int = 1
    endpoint_name: str = "user.getRecentTracks"

    def method_name(self) -> str:
        return "user.getRecentTracks"

    def build_params(self) -> Dict[str, Any]:
        return {"user": self.user, "limit": self.limit, "page": self.page}
