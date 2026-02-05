"""
Shared Weaviate connection utilities.

This module handles:
- Environment variable validation
- API key to header mapping for all supported providers
- Client connection with automatic header configuration

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

import weaviate
from weaviate.classes.init import Auth
from weaviate.client import WeaviateClient

# Environment variable to Weaviate header mapping
# Supports both APIKEY and API_KEY variants
API_KEY_MAP = {
    # Anthropic
    "ANTHROPIC_APIKEY": "X-Anthropic-Api-Key",
    "ANTHROPIC_API_KEY": "X-Anthropic-Api-Key",
    # Anyscale
    "ANYSCALE_APIKEY": "X-Anyscale-Api-Key",
    "ANYSCALE_API_KEY": "X-Anyscale-Api-Key",
    # AWS
    "AWS_ACCESS_KEY": "X-Aws-Access-Key",
    "AWS_SECRET_KEY": "X-Aws-Secret-Key",
    # Cohere
    "COHERE_APIKEY": "X-Cohere-Api-Key",
    "COHERE_API_KEY": "X-Cohere-Api-Key",
    # Databricks
    "DATABRICKS_TOKEN": "X-Databricks-Token",
    # Friendli
    "FRIENDLI_TOKEN": "X-Friendli-Api-Key",
    # Google Vertex AI
    "VERTEX_APIKEY": "X-Goog-Vertex-Api-Key",
    "VERTEX_API_KEY": "X-Goog-Vertex-Api-Key",
    # Google AI Studio
    "STUDIO_APIKEY": "X-Goog-Studio-Api-Key",
    "STUDIO_API_KEY": "X-Goog-Studio-Api-Key",
    # HuggingFace
    "HUGGINGFACE_APIKEY": "X-HuggingFace-Api-Key",
    "HUGGINGFACE_API_KEY": "X-HuggingFace-Api-Key",
    # Jina AI
    "JINAAI_APIKEY": "X-JinaAI-Api-Key",
    "JINAAI_API_KEY": "X-JinaAI-Api-Key",
    # Mistral
    "MISTRAL_APIKEY": "X-Mistral-Api-Key",
    "MISTRAL_API_KEY": "X-Mistral-Api-Key",
    # NVIDIA
    "NVIDIA_APIKEY": "X-Nvidia-Api-Key",
    "NVIDIA_API_KEY": "X-Nvidia-Api-Key",
    # OpenAI
    "OPENAI_APIKEY": "X-OpenAI-Api-Key",
    "OPENAI_API_KEY": "X-OpenAI-Api-Key",
    # Azure OpenAI
    "AZURE_APIKEY": "X-Azure-Api-Key",
    "AZURE_API_KEY": "X-Azure-Api-Key",
    # Voyage AI
    "VOYAGE_APIKEY": "X-Voyage-Api-Key",
    "VOYAGE_API_KEY": "X-Voyage-Api-Key",
    # xAI
    "XAI_APIKEY": "X-Xai-Api-Key",
    "XAI_API_KEY": "X-Xai-Api-Key",
}


def validate_env(require_weaviate: bool = True) -> tuple[str, str]:
    """
    Validate required Weaviate environment variables.

    Args:
        require_weaviate: If True, exit with error if WEAVIATE_URL/API_KEY not set

    Returns:
        Tuple of (weaviate_url, weaviate_api_key)

    Raises:
        SystemExit: If required variables are missing
    """
    url = os.environ.get("WEAVIATE_URL", "").strip()
    api_key = os.environ.get("WEAVIATE_API_KEY", "").strip()

    if require_weaviate:
        if not url:
            print("Error: WEAVIATE_URL environment variable not set", file=sys.stderr)
            sys.exit(1)
        if not api_key:
            print(
                "Error: WEAVIATE_API_KEY environment variable not set", file=sys.stderr
            )
            sys.exit(1)

    return url, api_key


def get_headers() -> dict[str, str] | None:
    """
    Build headers dict from all available API keys in environment.

    Scans environment for all known API key variables and builds
    the appropriate headers dict for Weaviate client connection.

    Returns:
        Dict of headers if any API keys found, None otherwise
    """
    headers = {}

    for env_var, header_name in API_KEY_MAP.items():
        value = os.environ.get(env_var, "").strip()
        if value:
            # Only add if we don't already have this header
            # (handles APIKEY vs API_KEY variants)
            if header_name not in headers:
                headers[header_name] = value

    return headers if headers else None


def get_detected_providers() -> list[str]:
    """
    Get list of provider names with detected API keys.

    Returns:
        List of provider names (e.g., ["OpenAI", "Cohere"])
    """
    providers = set()
    provider_map = {
        "X-Anthropic-Api-Key": "Anthropic",
        "X-Anyscale-Api-Key": "Anyscale",
        "X-Aws-Access-Key": "AWS",
        "X-Cohere-Api-Key": "Cohere",
        "X-Databricks-Token": "Databricks",
        "X-Friendli-Api-Key": "Friendli",
        "X-Goog-Vertex-Api-Key": "Google Vertex AI",
        "X-Goog-Studio-Api-Key": "Google AI Studio",
        "X-HuggingFace-Api-Key": "HuggingFace",
        "X-JinaAI-Api-Key": "Jina AI",
        "X-Mistral-Api-Key": "Mistral",
        "X-Nvidia-Api-Key": "NVIDIA",
        "X-OpenAI-Api-Key": "OpenAI",
        "X-Azure-Api-Key": "Azure OpenAI",
        "X-Voyage-Api-Key": "Voyage AI",
        "X-Xai-Api-Key": "xAI",
    }

    headers = get_headers()
    if headers:
        for header_name in headers:
            if header_name in provider_map:
                providers.add(provider_map[header_name])

    return sorted(providers)


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
    if url is None or api_key is None:
        env_url, env_api_key = validate_env()
        url = url or env_url
        api_key = api_key or env_api_key

    # Auto-detect headers if not provided
    if headers is None:
        headers = get_headers()

    if verbose:
        providers = get_detected_providers()
        if providers:
            print(f"Detected API keys: {', '.join(providers)}", file=sys.stderr)
        print("Connecting to Weaviate...", file=sys.stderr)

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=url,
        auth_credentials=Auth.api_key(api_key),
        headers=headers,
    )

    try:
        if verbose:
            print("Connected.", file=sys.stderr)
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
    if url is None or api_key is None:
        env_url, env_api_key = validate_env()
        url = url or env_url
        api_key = api_key or env_api_key

    if headers is None:
        headers = get_headers()

    if verbose:
        providers = get_detected_providers()
        if providers:
            print(f"Detected API keys: {', '.join(providers)}", file=sys.stderr)
        print("Connecting to Weaviate...", file=sys.stderr)

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=url,
        auth_credentials=Auth.api_key(api_key),
        headers=headers,
    )

    if verbose:
        print("Connected.", file=sys.stderr)

    return client
