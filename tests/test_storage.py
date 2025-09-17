from __future__ import annotations

import json
from unittest.mock import MagicMock

from src.ingestion.config import S3Settings
from src.ingestion.storage import S3Storage


def test_partition_key_stable_prefix():
    key = S3Storage.partition_key("chart.getTopArtists")
    assert key.startswith("chart.getTopArtists/dt=")
    assert key.endswith(".json")


def test_put_json_invokes_boto3_and_validate_bucket():
    settings = S3Settings(
        enpoint_url="http://minio:9000",
        region_name="us-east-1",
        access_key="minio",
        secret_key="minio123",
        bucket_raw="bronze",
    )
    storage = S3Storage(settings)
    fake_client = MagicMock()
    storage._client = fake_client

    fake_client.head_bucket.return_value = None

    storage.put_json("bucket", "k", {"ok": True})
    fake_client.head_bucket.assert_called_once_with(Bucket="bucket")
    args, kwargs = fake_client.put_object.call_args
    assert kwargs["Bucket"] == "bucket"
    assert kwargs["Key"] == "k"
    body = kwargs["Body"]
    assert json.loads(body.decode("utf-8")) == {"ok": True}
