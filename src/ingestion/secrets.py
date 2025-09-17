"""
Secrets providers (Vault, Env fallback) used by extractors.
We keep a small interface, so switching from Vault dev to Vault
server/AppRole or plain env vars is easier.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
import requests

from src.ingestion.exception import ConfigError

LOG = logging.getLogger(__name__)

load_dotenv(dotenv_path="../../infra/.env")


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
        return f"{self.addr}/v1/{self.kv_mount}/{path}"

    def get(self, path: str, key: str) -> Optional[str]:
        try:
            resp = requests.get(
                self._url(path),
                headers={"X-Vault-Token": self.token},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data: Any = resp.json()
            return data.get("data", {}).get(key)
        except requests.exceptions.RequestException:
            return None


class CachedSecretProvider(SecretsProvider):
    inner: SecretsProvider
    _cache: dict[str, Optional[str]] = field(default_factory=dict)

    def get(self, path: str, key: str) -> Optional[str]:
        ck = f"{path}:{key}"
        if ck not in self._cache:
            self._cache[ck] = self.inner.get(path, key)
        return self._cache[ck]


def resolve_lastfm_api_key(provider: SecretsProvider) -> Optional[str]:
    """Get the Last.fm API key from the provider or raise a clear error."""
    try:
        api_key = provider.get("lastfm", "api-key")
    except Exception as e:
        LOG.error("Secrets error resolving Last.fm API key: %s", e)
        raise ConfigError(
            "Missing Last.fm API key (secrets provider failed)"
        ) from e
    if not api_key or not api_key.strip():
        raise ConfigError("Missing Last.fm API key (empty)")
    LOG.debug("Resolved Last.fm API key (masked)")
    return api_key
