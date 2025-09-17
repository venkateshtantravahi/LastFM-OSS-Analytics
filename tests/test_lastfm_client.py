from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.exception import AuthError, RateLimitError, UpstreamError
from src.ingestion.lastfm_client import LastFMClient


@patch("src.ingestion.lastfm_client.requests.Session")
def test_client_passes_method_and_key(MockSession):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok"}

    session = MockSession.return_value
    session.get.return_value = mock_resp

    client = LastFMClient(api_key="ABC")
    out = client.get("chart.getTopArtists", limit=5)
    assert out == {"status": "ok"}

    args, kwargs = session.get.call_args
    assert args[0].endswith("/2.0/"), "Should call the Last.fm API base URL"
    params = kwargs["params"]
    assert params["method"] == "chart.getTopArtists"
    assert params["api_key"] == "ABC"
    assert params["format"] == "json"
    assert params["limit"] == 5


@patch("src.ingestion.lastfm_client.requests.Session")
def test_maps_http_401_to_auth_error(MockSession):
    mock_resp = MagicMock(status_code=401)
    mock_resp.json.return_value = {}
    MockSession.return_value.get.return_value = mock_resp

    client = LastFMClient(api_key="ABC")
    with pytest.raises(AuthError):
        client.get("chart.getTopArtists", limit=1)


@patch("src.ingestion.lastfm_client.requests.Session")
def test_maps_http_5xx_to_upstream_error(MockSession):
    mock_resp = MagicMock(status_code=503)
    mock_resp.json.return_value = {}
    MockSession.return_value.get.return_value = mock_resp

    client = LastFMClient(api_key="ABC")
    with pytest.raises(UpstreamError):
        client.get("chart.getTopArtists", limit=1)


@patch("src.ingestion.lastfm_client.requests.Session")
def test_maps_json_error_code_to_rate_limit(MockSession):
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {
        "error": 29,
        "message": "Rate limit exceeded",
    }
    MockSession.return_value.get.return_value = mock_resp

    client = LastFMClient(api_key="ABC")
    with pytest.raises(RateLimitError):
        client.get("chart.getTopArtists", limit=1)
