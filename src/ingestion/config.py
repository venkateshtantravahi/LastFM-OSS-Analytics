"""
Configuration objects for the ingestion package.

Uses Pydantic BaseSettings so env vars in infra/.env automatically
populate at runtime both locally and in Airflow containers.
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    """S3/MinIO settings for object storage.
    Environment variables accepted:
    - S3_ENDPOINT, S3_REGION, S3_BUCKET_RAW, S3_BUCKET_CURATED
    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (or MINIO_ROOT_USER/PASSWORD)
    """

    endpoint_url: str = Field("http://localhost:9000", alias="S3_ENDPOINT")
    region_name: str = Field("us-east-1", alias="S3_REGION")
    access_key: str = Field("minio", alias="AWS_ACCESS_KEY_ID")
    secret_key: str = Field("minio123", alias="AWS_SECRET_ACCESS_KEY")
    bucket_raw: str = Field("lastfm-raw", alias="S3_BUCKET_RAW")
    bucket_curated: str = Field("lastfm-curated", alias="S3_BUCKET_CURATED")

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _require_non_empty(self):
        for name in ("endpoint_url", "bucket_raw", "access_key", "secret_key"):
            v = getattr(self, name, None)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"{name} must be non-empty and set")
        return self

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )


class VaultSettings(BaseSettings):
    """HashiCorp Vault dev-mode access settings"""

    addr: Optional[str] = Field("http://127.0.0.1:8200", alias="VAULT_ADDR")
    token: Optional[str] = Field("dev-root", alias="VAULT_DEV_ROOT_TOKEN_ID")
    kv_mount: str = Field("kv", alias="VAULT_KV_MOUNT")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class AppSettings(BaseSettings):
    """Top-level application configuration.
    Nested settings are independent `BaseSettings` models; instantiating them
    loads their respective env vars.
    """

    s3: S3Settings = Field(default_factory=S3Settings)
    vault: VaultSettings = Field(default_factory=VaultSettings)
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )

    def assert_runtime_ready(self) -> None:
        missing = []
        for name in (
            "endpoint_url",
            "region_name",
            "access_key",
            "secret_key",
            "bucket_raw",
        ):
            if not getattr(self.s3, name, None):
                missing.append(f"s3.{name}")
            if not self.vault.addr or not self.vault.token:
                missing.append("vault.addr/token")
        if missing:
            from src.ingestion.exception import ConfigError

            raise ConfigError(
                f"Missing required settings: {', '.join(missing)}"
            )
