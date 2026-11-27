"""
Shared Weaviate connection utilities.

This module handles:
- Environment variable validation
- API key to header mapping for all supported providers
- Client connection with automatic header configuration
- Routing WEAVIATE_URL to the right connection helper:
    * Weaviate Cloud   (*.weaviate.cloud / *.weaviate.network) -> connect_to_weaviate_cloud
    * Local Docker     (localhost / 127.0.0.1 over http)       -> connect_to_local
    * Self-hosted      (any other host)                        -> connect_to_custom

Environment variables:
    WEAVIATE_URL           Cluster / server URL (required)
    WEAVIATE_API_KEY       API key (required for Weaviate Cloud, optional otherwise)
    WEAVIATE_GRPC_HOST     gRPC host if different from the URL host (non-cloud only)
    WEAVIATE_GRPC_PORT     gRPC port (default 50051; 443 for secure custom setups)
    WEAVIATE_GRPC_SECURE   true/false, default: same as the URL scheme (custom only)

Usage in scripts:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
    from weaviate_conn import get_client, get_headers, validate_env
"""

import os
import sys
from contextlib import contextmanager
from typing import Generator
from urllib.parse import urlparse

import weaviate
from weaviate.classes.init import Auth
from weaviate.client import WeaviateClient
from weaviate.classes.init import AdditionalConfig, Timeout

# Canonical environment variable to Weaviate header mapping
API_KEY_MAP = {
    "ANTHROPIC_API_KEY": "X-Anthropic-Api-Key",
    "ANYSCALE_API_KEY": "X-Anyscale-Api-Key",
    "AWS_ACCESS_KEY": "X-Aws-Access-Key",
    "AWS_SECRET_KEY": "X-Aws-Secret-Key",
    "COHERE_API_KEY": "X-Cohere-Api-Key",
    "DATABRICKS_TOKEN": "X-Databricks-Token",
    "FRIENDLI_TOKEN": "X-Friendli-Api-Key",
    "VERTEX_API_KEY": "X-Goog-Vertex-Api-Key",
    "STUDIO_API_KEY": "X-Goog-Studio-Api-Key",
    "HUGGINGFACE_API_KEY": "X-HuggingFace-Api-Key",
    "JINAAI_API_KEY": "X-JinaAI-Api-Key",
    "MISTRAL_API_KEY": "X-Mistral-Api-Key",
    "NVIDIA_API_KEY": "X-Nvidia-Api-Key",
    "OPENAI_API_KEY": "X-OpenAI-Api-Key",
    "AZURE_API_KEY": "X-Azure-Api-Key",
    "VOYAGE_API_KEY": "X-Voyage-Api-Key",
    "XAI_API_KEY": "X-Xai-Api-Key",
}


def _collect_headers_and_providers() -> tuple[dict[str, str], list[str]]:
    """
    Scan env once to build Weaviate headers and detected key names.

    Returns:
        Tuple of (headers, detected_env_var_names)
    """
    headers: dict[str, str] = {}
    detected_providers: list[str] = []

    for env_var, header_name in API_KEY_MAP.items():
        value = os.environ.get(env_var, "").strip()
        if not value:
            continue

        detected_providers.append(env_var)
        headers[header_name] = value

    return headers, detected_providers


_CLOUD_SUFFIXES = (".weaviate.cloud", ".weaviate.network")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _parse_url(url: str) -> tuple[str, str, int | None]:
    """
    Split a WEAVIATE_URL into (scheme, host, port).

    A bare host such as ``localhost:8080`` or ``my-cluster.weaviate.cloud`` is
    accepted: loopback hosts default to http, everything else to https.
    """
    url = url.strip()
    if "://" not in url:
        is_loopback = url.lower().startswith(("localhost", "127.0.0.1", "[::1]"))
        url = ("http://" if is_loopback else "https://") + url

    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError(f"Cannot parse a host from WEAVIATE_URL={url!r}")
    try:
        port = parsed.port
    except ValueError as e:
        raise ValueError(f"Invalid port in WEAVIATE_URL={url!r}: {e}") from e
    return parsed.scheme.lower(), parsed.hostname.lower(), port


def is_cloud_url(url: str) -> bool:
    """True when the URL points at a Weaviate Cloud cluster."""
    return _parse_url(url)[1].endswith(_CLOUD_SUFFIXES)


def _env_int(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from None


def _env_bool(name: str) -> bool | None:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return None
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be true or false, got {raw!r}")


def _resolve_credentials(url: str | None, api_key: str | None) -> tuple[str, str]:
    """
    Fill in missing url/api_key from the environment and enforce requirements.

    WEAVIATE_URL is always required. WEAVIATE_API_KEY is required only for
    Weaviate Cloud; local and self-hosted servers often allow anonymous access.
    """
    if url is None:
        url = os.environ.get("WEAVIATE_URL", "").strip()
    if not url:
        print("Error: WEAVIATE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    if api_key is None:
        api_key = os.environ.get("WEAVIATE_API_KEY", "").strip()
    if not api_key and is_cloud_url(url):
        print(
            "Error: WEAVIATE_API_KEY environment variable not set "
            "(required for Weaviate Cloud)",
            file=sys.stderr,
        )
        sys.exit(1)

    return url, api_key


def validate_env(require_weaviate: bool = True) -> tuple[str, str]:
    """
    Validate required Weaviate environment variables.

    Args:
        require_weaviate: If True, exit with error if WEAVIATE_URL is not set,
            or if WEAVIATE_API_KEY is not set for a Weaviate Cloud URL

    Returns:
        Tuple of (weaviate_url, weaviate_api_key). The key may be an empty
        string for local / self-hosted servers.

    Raises:
        SystemExit: If required variables are missing
    """
    if require_weaviate:
        return _resolve_credentials(None, None)

    return (
        os.environ.get("WEAVIATE_URL", "").strip(),
        os.environ.get("WEAVIATE_API_KEY", "").strip(),
    )


def _open_connection(
    url: str,
    api_key: str,
    headers: dict[str, str] | None,
) -> tuple[WeaviateClient, str]:
    """
    Open a client using the helper that matches the URL. Returns (client, mode).
    """
    config = AdditionalConfig(timeout=Timeout(init=30, query=60, insert=120))
    auth = Auth.api_key(api_key) if api_key else None
    scheme, host, port = _parse_url(url)

    if is_cloud_url(url):
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=auth,
            headers=headers,
            additional_config=config,
        )
        return client, "cloud"

    grpc_host_env = os.environ.get("WEAVIATE_GRPC_HOST", "").strip()
    grpc_port_env = _env_int("WEAVIATE_GRPC_PORT")
    grpc_secure_env = _env_bool("WEAVIATE_GRPC_SECURE")

    if scheme == "http" and host in _LOCAL_HOSTS and not grpc_host_env:
        client = weaviate.connect_to_local(
            host=host,
            port=port or 8080,
            grpc_port=grpc_port_env or 50051,
            headers=headers,
            auth_credentials=auth,
            additional_config=config,
        )
        return client, "local"

    secure = scheme == "https"
    grpc_secure = secure if grpc_secure_env is None else grpc_secure_env
    client = weaviate.connect_to_custom(
        http_host=host,
        http_port=port or (443 if secure else 80),
        http_secure=secure,
        grpc_host=grpc_host_env or host,
        grpc_port=grpc_port_env or (443 if grpc_secure else 50051),
        grpc_secure=grpc_secure,
        headers=headers,
        auth_credentials=auth,
        additional_config=config,
    )
    return client, "custom"


def get_headers() -> dict[str, str] | None:
    """
    Build headers dict from all available API keys in environment.

    Scans environment for all known API key variables and builds
    the appropriate headers dict for Weaviate client connection.

    Returns:
        Dict of headers if any API keys found, None otherwise
    """
    headers, _ = _collect_headers_and_providers()
    return headers if headers else None


def get_detected_providers() -> list[str]:
    """
    Get list of detected API key environment variable names.

    Returns:
        List of env var names (e.g., ["OPENAI_API_KEY", "COHERE_API_KEY"])
    """
    _, detected_providers = _collect_headers_and_providers()
    return sorted(detected_providers)


@contextmanager
def get_client(
    url: str | None = None,
    api_key: str | None = None,
    headers: dict[str, str] | None = None,
    verbose: bool = True,
) -> Generator[WeaviateClient, None, None]:
    """
    Context manager for Weaviate client connection.

    Auto-detects credentials from environment if not provided.
    Auto-builds headers from all available API keys if not provided.

    Args:
        url: Weaviate cluster URL (default: from WEAVIATE_URL env var)
        api_key: Weaviate API key (default: from WEAVIATE_API_KEY env var)
        headers: Custom headers dict (default: auto-detected from env vars)
        verbose: Print connection status to stderr

    Yields:
        Connected WeaviateClient instance

    Example:
        with get_client() as client:
            collections = client.collections.list_all()
    """
    # Get credentials from env if not provided
    url, api_key = _resolve_credentials(url, api_key)

    # Auto-detect headers if not provided
    if headers is None:
        headers, detected_providers = _collect_headers_and_providers()
        headers = headers or None
    else:
        detected_providers = None

    if verbose:
        detected = sorted(detected_providers) if detected_providers is not None else []
        if detected:
            print(f"Detected providers: {', '.join(detected)}", file=sys.stderr)
        print("Connecting to Weaviate...", file=sys.stderr)

    client, mode = _open_connection(url, api_key, headers)

    try:
        if verbose:
            print(f"Connected ({mode}).", file=sys.stderr)
        yield client
    finally:
        client.close()


def connect_client(
    url: str | None = None,
    api_key: str | None = None,
    headers: dict[str, str] | None = None,
    verbose: bool = True,
) -> WeaviateClient:
    """
    Get a Weaviate client connection (non-context manager version).

    IMPORTANT: Caller is responsible for calling client.close()

    Args:
        url: Weaviate cluster URL (default: from WEAVIATE_URL env var)
        api_key: Weaviate API key (default: from WEAVIATE_API_KEY env var)
        headers: Custom headers dict (default: auto-detected from env vars)
        verbose: Print connection status to stderr

    Returns:
        Connected WeaviateClient instance
    """
    url, api_key = _resolve_credentials(url, api_key)

    if headers is None:
        headers, detected_providers = _collect_headers_and_providers()
        headers = headers or None
    else:
        detected_providers = None

    if verbose:
        detected = sorted(detected_providers) if detected_providers is not None else []
        if detected:
            print(f"Detected providers: {', '.join(detected)}", file=sys.stderr)
        print("Connecting to Weaviate...", file=sys.stderr)

    client, mode = _open_connection(url, api_key, headers)

    if verbose:
        print(f"Connected ({mode}).", file=sys.stderr)

    return client
