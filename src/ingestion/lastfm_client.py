from __future__ import annotations

import os
from typing import Any, Dict

import requests

API = "https://ws.audioscrobbler.com/2.0/"


class LastFM:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("LASTFM_API_KEY")
        assert self.api_key, "Set LASTFM_API_KEY or fetch from Vault"

    def _get(self, params: Dict[str, Any]):
        p = {"api_key": self.api_key, "format": "json", **params}
        r = requests.get(API, params=p, timeout=30)
        r.raise_for_status()
        return r.json()

    def recent_tracks(self, user: str, limit: int = 200, page: int = 1):
        return self._get(
            {
                "method": "user.getRecentTracks",
                "user": user,
                "limit": limit,
                "page": page,
            }
        )
