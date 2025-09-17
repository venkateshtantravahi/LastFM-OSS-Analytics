"""Minimal, robust Last.fm API client with retry/backoff.
Docs: https://www.last.fm/api
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.ingestion.exception import (
    AuthError,
    ConfigError,
    RateLimitError,
    UpstreamError,
)

API_BASE = "https://ws.audioscrobbler.com/2.0/"
LOG = logging.getLogger(__name__)

LASTFM_RETRYABLE_CODES = {16, 29}  # temp error, rate limit
LASTFM_AUTH_CODES = {
    4,
    9,
    10,
    26,
}  # auth failed, invalid session/api key, suspended
LASTFM_STATUS_FORCE_LIST = [429, 500, 502, 503, 504]


def _mk_session(timeout: int = 15) -> requests.Session:
    """Create a requests session with retry/backoff on 429/5xx
    and a UA header."""
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.8,
        status_forcelist=LASTFM_STATUS_FORCE_LIST,
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "lastfm-oss-analytics/1.0"})
    return s


class LastFMClient:
    """
    HTTP client to call Last.fm API methods.

    Parameters
    ---------
    api_key: str
        Last.fm API key.
    timeout_s: int
        timeout seconds for calling Last.fm API.
    """

    def __init__(self, api_key: Optional[str] = None, timeout_s: int = 30):
        if not api_key:
            raise ConfigError("Missing LASTFM_API_KEY (env or vault).")
        self.api_key = api_key
        self.timeout_s = timeout_s
        self._session = _mk_session(timeout=timeout_s)

    def _request(self, params: Dict[str, Any], *, max_retries: int = 5):
        """Single request (retries handled by the session adapter)."""
        p = {"api_key": self.api_key, "format": "json", **params}
        method = str(p.get("method", "<missing>"))
        try:
            response = self._session.get(
                API_BASE, params=p, timeout=self.timeout_s
            )
        except (requests.ConnectionError, requests.Timeout) as e:
            raise UpstreamError(str(e))

        if response.status_code == 401:
            raise AuthError("Unauthorized (HTTP 401)")
        if response.status_code == 429:
            raise RateLimitError("Too Many Requests")
        if response.status_code >= 500:
            raise UpstreamError(
                f"HTTP {response.status_code} from Last.fm API server error"
            )

        try:
            data = response.json()
        except Exception as e:
            LOG.error(
                "Non-Json response for %s: %s", method, response.text[:256]
            )
            raise UpstreamError(
                f"Invalid Json from Last.fm API response from {e}"
            )

        if isinstance(data, dict) and "error" in data:
            code = int(data.get("error"))
            msg = str(data.get("message", ""))
            if code in LASTFM_AUTH_CODES:
                raise AuthError(f"Last.fm auth error {code}: {msg}")
            if code in LASTFM_RETRYABLE_CODES:
                raise RateLimitError(f"Last.fm retryable error {code}: {msg}")
            raise UpstreamError(f"Last.fm error {code}: {msg}")

        LOG.debug(
            "Last.fm OK %s params=%s",
            method,
            {k: v for k, v in p.items() if k != "api_key"},
        )
        return data

    def get(self, method: str, **kwargs: Any) -> Dict[str, Any]:
        return self._request({"method": method, **kwargs})
