"""S3/MinIO storage utilities with a small, testable interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import logging
from typing import Any, Dict, Optional
import uuid

import boto3
import botocore
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from src.ingestion.config import S3Settings
from src.ingestion.exception import StorageError

LOG = logging.getLogger(__name__)


@dataclass
class S3Storage:
    """Thin wrapper over boto3 for JSON object writes."""

    settings: S3Settings
    _client: Optional[BaseClient] = None

    def _ensure_client(self) -> None:
        """Create the boto3 client lazily (idempotent)."""
        if self._client is None:
            cfg = botocore.config.Config(
                retries={"max_attempts": 5, "mode": "standard"},
                connect_timeout=10,
                read_timeout=30,
            )
            self._client = boto3.client(
                "s3",
                endpoint_url=self.settings.endpoint_url,
                aws_access_key_id=self.settings.access_key,
                aws_secret_access_key=self.settings.secret_key,
                region_name=self.settings.region_name,
                config=cfg,
            )

    @property
    def client(self) -> BaseClient:
        self._ensure_client()
        return self._client

    def validate_bucket(self, bucket: str) -> None:
        """Fail fast if the bucket is not reachable."""
        try:
            self.client.head_bucket(Bucket=bucket)
        except ClientError as e:
            LOG.error("S3 head_bucket failed for %s", bucket, exc_info=True)
            raise StorageError(f"S3 bucket not accessible: {bucket}") from e
        except Exception as e:
            LOG.error(
                "S3 head_bucket unexpected error for %s", bucket, exc_info=True
            )
            raise StorageError(f"S3 bucket check failed: {bucket}") from e

    def put_json(self, bucket: str, key: str, payload: Dict[str, Any]) -> None:
        try:
            body = json.dumps(
                payload, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            self._ensure_client()
            self.validate_bucket(bucket)
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
            LOG.info("Wrote s3://%s/%s bytes=%d", bucket, key, len(body))
        except Exception as e:
            LOG.error("S3 write failed s3://%s/%s", bucket, key, exc_info=True)
            raise StorageError(str(e))

    @staticmethod
    def partition_key(endpoint: str, d: Optional[date] = None) -> str:
        d = d or date.today()
        return f"{endpoint}/dt={d:%Y-%m-%d}/part-{uuid.uuid4()}.json"
