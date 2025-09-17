# # tests/test_run_extract.py
# from types import SimpleNamespace as NS
# from unittest.mock import patch
#
# from src.ingestion.config import AppSettings
# import src.ingestion.run_extract as rx
#
#
# class FakeExtractor:
#     """Minimal stand-in to capture constructor args."""
#
#     constructed_with = None
#
#     def __init__(self, *args, **kwargs):
#         FakeExtractor.constructed_with = (args, kwargs)
#
#
# def test__resolve_api_key_prefers_env(monkeypatch):
#   """_resolve_api_key should return the env provider's value before Vault."""
#
#     class _EnvProv:
#         def get(self, key):
#             assert key == "LASTFM_API_KEY"
#             return "ENVKEY"
#
#     class _VaultProv:
#         def __init__(self, *_args, **_kwargs):
#             pass
#
#         def get(self, key):
#             # Would only be called if env provider failed
#             return "VAULTKEY"
#
#     # Patch providers on the module under test (no real env or Vault used)
#     monkeypatch.setattr(
#         rx, "EnvSecretsProvider", lambda: _EnvProv(), raising=True
#     )
#     monkeypatch.setattr(
#         rx, "VaultKV2Provider", lambda **_kw: _VaultProv(), raising=True
#     )
#
#     key = rx._resolve_api_key(AppSettings())
#     assert key == "ENVKEY"
#
#
# @patch("src.ingestion.run_extract.S3Storage")
# @patch("src.ingestion.run_extract.LastFMClient")
# def test_build_extractor_wires_client_and_storage(
#     lastfm_client, s3storage, monkeypatch
# ):
#     """build_extractor should build LastFMClient with the resolved key and
#     S3Storage from settings, then pass both (via a context) plus
#     args into the extractor from the registry.
#     """
#     # Force API key resolution path to a deterministic value
#     monkeypatch.setattr(
#         rx, "_resolve_api_key", lambda _settings: "ENVKEY", raising=True
#     )
#
#     # Use our fake extractor so we don't depend on real class implementations
#     monkeypatch.setattr(
#         rx,
#         "EXTRACTOR_REGISTRY",
#         {"chart_top_artists": FakeExtractor},
#         raising=True,
#     )
#
#     settings = AppSettings()
#     args = NS(limit=10, country="india", user="rj", page=1)
#
#     extractor = rx.build_extractor(settings, "chart_top_artists", args)
#
#     # Client and storage constructed with expected inputs
#     lastfm_client.assert_called_once_with(api_key="ENVKEY")
#     s3storage.assert_called_once_with(settings.s3)
#
#     # Extractor constructed with (context, args)
#     assert isinstance(extractor, FakeExtractor)
#     (pos, kw) = FakeExtractor.constructed_with
#     assert kw == {}
#     ctx, passed_args = pos
#     assert hasattr(ctx, "client") and hasattr(ctx, "storage")
#     assert ctx.client is lastfm_client.return_value
#     assert ctx.storage is s3storage.return_value
#     assert passed_args is args
