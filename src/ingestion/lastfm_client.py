"""Minimal, robust Last.fm API client with retry/backoff.
Docs: https://www.last.fm/api
"""

from __future__ import annotations

import time
from typing import Any, Dict, Mapping

import requests

API_BASE = "https://ws.audioscrobbler.com/2.0/"


class LastFMClient:
    """
    HTTP client to call Last.fm API methods.

    Parameters
    ---------
    api_key: str
        Last.fm API key.
    max_retries: int
        How many times to retry on transient HTTP failures.
    backoff_sec: float
        Base backoff seconds (exponential with jitter).
    """

    def __init__(
        self, api_key: str, max_retries: int = 3, backoff_sec: float = 1.0
    ):
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_sec = backoff_sec

    def get(self, method: str, **params: Mapping[str, Any]) -> Dict[str, Any]:
        p = {
            "method": method,
            "api_key": self.api_key,
            "format": "json",
            **params,
        }
        attempt = 0
        while True:
            try:
                resp = requests.get(API_BASE, params=p, timeout=30)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                sleep = self.backoff_sec * (2 ** (attempt - 1))
                time.sleep(sleep)
