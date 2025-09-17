from __future__ import annotations


class ExtractorError(Exception):
    """Base class for ingestion errors."""


class ConfigError(ExtractorError):
    """Bad/missing configuration (e.g., no API key)."""


class AuthError(ExtractorError):
    """Authentication/authorization problems (invalid/suspended key)."""


class RateLimitError(ExtractorError):
    """429 / Last.fm 29 rate-limited; may be retried."""


class UpstreamError(ExtractorError):
    """Any other upstream API error."""


class StorageError(ExtractorError):
    """S3/MinIO write failures."""
