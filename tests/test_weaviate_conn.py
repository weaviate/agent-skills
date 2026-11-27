"""Offline tests for URL routing in skills/weaviate/scripts/weaviate_conn.py.

Run:  uv run --with weaviate-client==4.23.1 --with pytest pytest tests/ -q
No Weaviate server is needed: the connect_to_* helpers are replaced by spies.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "skills" / "weaviate" / "scripts")
)

import weaviate  # noqa: E402
import weaviate_conn as wc  # noqa: E402

ENV_VARS = [
    "WEAVIATE_URL",
    "WEAVIATE_API_KEY",
    "WEAVIATE_GRPC_HOST",
    "WEAVIATE_GRPC_PORT",
    "WEAVIATE_GRPC_SECURE",
    "OPENAI_API_KEY",
]


class FakeClient:
    closed = False

    def close(self):
        self.closed = True


@pytest.fixture
def spy(monkeypatch):
    for v in ENV_VARS:
        monkeypatch.delenv(v, raising=False)
    calls = []

    def make(name):
        def _fn(**kwargs):
            calls.append((name, kwargs))
            return FakeClient()

        return _fn

    for name in ("connect_to_weaviate_cloud", "connect_to_local", "connect_to_custom"):
        monkeypatch.setattr(weaviate, name, make(name))
    return calls


def connect(monkeypatch, url, **env):
    monkeypatch.setenv("WEAVIATE_URL", url)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    with wc.get_client(verbose=False):
        pass


def test_cloud_url_still_uses_cloud_helper(spy, monkeypatch):
    connect(monkeypatch, "https://abc.c0.europe-west3.gcp.weaviate.cloud", WEAVIATE_API_KEY="k")
    name, kw = spy[0]
    assert name == "connect_to_weaviate_cloud"
    assert kw["cluster_url"] == "https://abc.c0.europe-west3.gcp.weaviate.cloud"
    assert kw["auth_credentials"] is not None


def test_cloud_without_api_key_exits(spy, monkeypatch, capsys):
    monkeypatch.setenv("WEAVIATE_URL", "https://abc.weaviate.cloud")
    with pytest.raises(SystemExit) as ei:
        wc.get_client(verbose=False).__enter__()
    assert ei.value.code == 1
    assert "WEAVIATE_API_KEY" in capsys.readouterr().err
    assert spy == []


def test_missing_url_exits(spy, capsys):
    with pytest.raises(SystemExit):
        wc.get_client(verbose=False).__enter__()
    assert "WEAVIATE_URL" in capsys.readouterr().err


def test_localhost_defaults_without_api_key(spy, monkeypatch):
    connect(monkeypatch, "http://localhost:8080")
    name, kw = spy[0]
    assert name == "connect_to_local"
    assert (kw["host"], kw["port"], kw["grpc_port"]) == ("localhost", 8080, 50051)
    assert kw["auth_credentials"] is None


def test_bare_localhost_and_default_port(spy, monkeypatch):
    connect(monkeypatch, "localhost")
    name, kw = spy[0]
    assert name == "connect_to_local" and kw["port"] == 8080


def test_local_custom_ports_and_optional_api_key(spy, monkeypatch):
    connect(
        monkeypatch,
        "http://127.0.0.1:8079",
        WEAVIATE_GRPC_PORT="50060",
        WEAVIATE_API_KEY="dev-key",
    )
    name, kw = spy[0]
    assert name == "connect_to_local"
    assert (kw["port"], kw["grpc_port"]) == (8079, 50060)
    assert kw["auth_credentials"] is not None


def test_self_hosted_https_defaults(spy, monkeypatch):
    connect(monkeypatch, "https://weaviate.internal.example.com")
    name, kw = spy[0]
    assert name == "connect_to_custom"
    assert kw["http_host"] == "weaviate.internal.example.com"
    assert (kw["http_port"], kw["http_secure"]) == (443, True)
    assert (kw["grpc_host"], kw["grpc_port"], kw["grpc_secure"]) == (
        "weaviate.internal.example.com",
        443,
        True,
    )


def test_self_hosted_http_with_separate_grpc(spy, monkeypatch):
    connect(
        monkeypatch,
        "http://10.0.0.5:8080",
        WEAVIATE_GRPC_HOST="grpc.internal",
        WEAVIATE_GRPC_PORT="50051",
        WEAVIATE_GRPC_SECURE="false",
    )
    name, kw = spy[0]
    assert name == "connect_to_custom"
    assert (kw["http_host"], kw["http_port"], kw["http_secure"]) == ("10.0.0.5", 8080, False)
    assert (kw["grpc_host"], kw["grpc_port"], kw["grpc_secure"]) == ("grpc.internal", 50051, False)


def test_localhost_with_separate_grpc_host_uses_custom(spy, monkeypatch):
    connect(monkeypatch, "http://localhost:8080", WEAVIATE_GRPC_HOST="grpc-proxy")
    assert spy[0][0] == "connect_to_custom"


def test_https_localhost_uses_custom(spy, monkeypatch):
    connect(monkeypatch, "https://localhost:8443")
    name, kw = spy[0]
    assert name == "connect_to_custom" and kw["http_secure"] is True


def test_provider_headers_forwarded_to_local(spy, monkeypatch):
    connect(monkeypatch, "http://localhost:8080", OPENAI_API_KEY="sk-test")
    assert spy[0][1]["headers"] == {"X-OpenAI-Api-Key": "sk-test"}


def test_timeouts_applied_to_every_mode_and_connect_client(spy, monkeypatch):
    monkeypatch.setenv("WEAVIATE_URL", "http://localhost:8080")
    wc.connect_client(verbose=False)
    assert spy[0][1]["additional_config"].timeout.insert == 120


@pytest.mark.parametrize("name,val", [("WEAVIATE_GRPC_PORT", "abc"), ("WEAVIATE_GRPC_SECURE", "maybe")])
def test_bad_env_values_raise_clear_error(spy, monkeypatch, name, val):
    monkeypatch.setenv("WEAVIATE_URL", "http://localhost:8080")
    monkeypatch.setenv(name, val)
    with pytest.raises(ValueError, match=name):
        wc.connect_client(verbose=False)


def test_client_closed_after_context(spy, monkeypatch):
    monkeypatch.setenv("WEAVIATE_URL", "http://localhost:8080")
    with wc.get_client(verbose=False) as c:
        assert not c.closed
    assert c.closed


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://abc.c0.europe-west3.gcp.weaviate.cloud", True),
        ("abc.weaviate.cloud", True),
        ("https://abc.weaviate.network", True),
        ("http://localhost:8080", False),
        ("https://weaviate.internal.example.com", False),
        ("https://notweaviate.cloud.example.com", False),
    ],
)
def test_is_cloud_url(url, expected):
    assert wc.is_cloud_url(url) is expected
