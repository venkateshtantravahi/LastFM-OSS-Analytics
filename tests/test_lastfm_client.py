from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.ingestion.lastfm_client import LastFMClient


@patch("src.ingestion.lastfm_client.requests.get")
def test_client_passes_method_and_key(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    client = LastFMClient(api_key="ABC")
    out = client.get("chart.getTopArtists", limit=5)
    assert out == {"status": "ok"}

    # Ensure params include method/api_key/format
    _, kwargs = mock_get.call_args
    params = kwargs["params"]
    assert params["method"] == "chart.getTopArtists"
    assert params["api_key"] == "ABC"
    assert params["format"] == "json"
    assert params["limit"] == 5
