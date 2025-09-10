"""
Configuration objects for the ingestion package.

Uses Pydantic BaseSettings so env vars in infra/.env automatically
populate at runtime both locally and in Airflow containers.
"""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    """S3/MinIO settings for object storage.
    Environment variables accepted:
    - S3_ENDPOINT, S3_REGION, S3_BUCKET_RAW, S3_BUCKET_CURATED
    - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (or MINIO_ROOT_USER/PASSWORD)
    """

    model_config = SettingsConfigDict(extra="ignore")

    enpoint_url: str = Field(
        "http://localhost:9000", validation_alias=AliasChoices("S3_ENDPOINT")
    )
    region_name: str = Field(
        "us-east-1", validation_alias=AliasChoices("S3_REGION")
    )
    access_key: str = Field(
        "admin",
        validation_alias=AliasChoices("AWS_ACCESS_KEY_ID", "MINIO_ROOT_USER"),
    )
    secret_key: str = Field(
        "adminadmin",
        validation_alias=AliasChoices(
            "AWS_SECRET_ACCESS_KEY", "MINIO_ROOT_PASSWORD"
        ),
    )
    bucket_raw: str = Field(
        "lastfm-raw", validation_alias=AliasChoices("S3_BUCKET_RAW")
    )
    bucket_curated: str = Field(
        "lastfm-curated", validation_alias=AliasChoices("S3_BUCKET_CURATED")
    )


class VaultSettings(BaseSettings):
    """HashiCorp Vault dev-mode access settings"""

    model_config = SettingsConfigDict(extra="ignore")
    addr: str = Field(
        "http://127.0.0.1:8200", validation_alias=AliasChoices("VAULT_ADDR")
    )
    token: str = Field(
        "dev-root", validation_alias=AliasChoices("VAULT_TOKEN")
    )
    kv_mount: str = Field(
        "kv", validation_alias=AliasChoices("VAULT_KV_MOUNT")
    )


class AppSettings(BaseSettings):
    """Top-level application configuration.
    Nested settings are independent `BaseSettings` models; instantiating them
    loads their respective env vars.
    """

    model_config = SettingsConfigDict(extra="ignore")
    log_level: str = Field("INFO", validation_alias=AliasChoices("LOG_LEVEL"))
    s3: S3Settings = S3Settings()
    vault: VaultSettings = VaultSettings()
