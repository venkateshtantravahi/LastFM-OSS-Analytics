from __future__ import annotations

from argparse import Namespace
from unittest.mock import patch

from src.ingestion.config import AppSettings
from src.ingestion.run_extract import build_extractor


@patch("src.ingestion.run_extract.resolve_lastfm_api_key")
@patch("src.ingestion.run_extract.VaultKV2Provider")
@patch("src.ingestion.run_extract.EnvSecretsProvider")
def test_build_extractor_prefers_env(
    env_provider, vault_provider, resolve_key
):
    # Arrange env provider to return a key so we do NOT call Vault
    env_instance = env_provider.return_value
    env_instance.get.return_value = "ENVKEY"

    settings = AppSettings()
    args = Namespace(
        job="chart_top_artists", limit=10, country="india", user="rj", page=1
    )

    # Act
    extractor = build_extractor(settings, "chart_top_artists", args)

    # Assert: no Vault call path used
    env_instance.get.assert_called()
    vault_provider.assert_not_called()
    resolve_key.assert_not_called()

    # And extractor has a client with the right key
    assert extractor.ctx.client.api_key == "ENVKEY"
