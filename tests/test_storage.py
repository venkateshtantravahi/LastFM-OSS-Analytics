from __future__ import annotations

import json
from unittest.mock import MagicMock

from src.ingestion.config import S3Settings
from src.ingestion.storage import S3Storage


def test_partition_key_stable_prefix():
    key = S3Storage.partition_key("chart.getTopArtists")
    assert key.startswith("chart.getTopArtists/dt=")
    assert key.endswith(".json")


def test_put_json_invokes_boto3():
    settings = S3Settings()
    storage = S3Storage(settings)
    fake_client = MagicMock()
    storage._client = fake_client

    storage.put_json("bucket", "k", {"ok": True})

    args, kwargs = fake_client.put_object.call_args
    assert kwargs["Bucket"] == "bucket"
    assert kwargs["Key"] == "k"
    body = kwargs["Body"]
    assert json.loads(body.decode("utf-8")) == {"ok": True}
