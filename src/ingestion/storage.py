"""S3/MinIO storage utilities with a small, testable interface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from typing import Any, Dict, Optional
import uuid

import boto3
from botocore.client import BaseClient

from .config import S3Settings


@dataclass
class S3Storage:
    """Thin wrapper over boto3 for JSON object writes."""

    settings: S3Settings
    _client: Optional[BaseClient] = None

    @property
    def client(self) -> BaseClient:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.settings.endpoint_url,
                aws_access_key_id=self.settings.aws_access_key,
                aws_secret_access_key=self.settings.aws_secret_key,
                region_name=self.settings.region_name,
            )
        return self._client

    def put_json(self, bucket: str, key: str, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.client.put_object(Bucket=bucket, Key=key, Body=body)

    @staticmethod
    def partition_key(endpoint: str, d: Optional[date] = None) -> str:
        d = d or date.today()
        return f"{endpoint}/dt={d:%Y-%m-%d}/part-{uuid.uuid4()}.json"
