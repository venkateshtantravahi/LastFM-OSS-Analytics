"""
Secrets providers (Vault, Env fallback) used by extractors.
We keep a small interface, so switching from Vault dev to Vault
server/AppRole or plain env vars is easier.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from typing import Any, Optional

import requests


class SecretsProvider(ABC):
    """Abstract base class for secrets providers."""

    @abstractmethod
    def get(self, path: str, key: str) -> Optional[str]:
        """Return the secret value (path, key), or None if not found."""


@dataclass
class EnvSecretProvider(SecretsProvider):
    """Read from environment variables."""

    prefix: str = ""

    def get(self, path: str, key: str) -> Optional[str]:
        env_key = f"{self.prefix}{key}" if self.prefix else key
        return os.getenv(env_key)


@dataclass
class VaultKV2Provider(SecretsProvider):
    """
    Very small Vault KVv2 client using raw HTTP (requests).
    Works in dev mode. For server mode, reuse the same API shape.
    """

    addr: str
    token: str
    kv_mount: str = "kv"
    timeout: float = 5.0

    def _url(self, path: str) -> str:
        return f"{self.addr}/v1/data/{self.kv_mount}/{path}"

    def get(self, path: str, key: str) -> Optional[str]:
        try:
            resp = requests.get(
                self._url(path),
                headers={"X-Vault-Token": self.token},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data: Any = resp.json()
            return data.get("data", {}).get("data", {}).get(key)
        except requests.exceptions.RequestException:
            return None


def resolve_lastfm_api_key(provider: SecretsProvider) -> Optional[str]:
    """Get the Last.fm API key from provider or raise a clear error."""
    key = provider.get("lastfm", "api_key")
    if not key:
        raise RuntimeError(
            """Last.fm API Key not found.
            Set env LASTFM_API_KEY environment variable or write
            kv/lastfm:api_key in vault"""
        )
    return key
