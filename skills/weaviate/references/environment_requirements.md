# Environment Requirements for Weaviate

Use this reference when building apps that connect to Weaviate and require external inference provider keys.

## Required Weaviate Auth

- `WEAVIATE_URL`
- `WEAVIATE_API_KEY` (required for Weaviate Cloud, optional for local / self-hosted servers)

## Connecting to Local or Self-Hosted Weaviate

The scripts choose the connection type from the host in `WEAVIATE_URL`:

| `WEAVIATE_URL` | Connection | Notes |
|----------------|------------|-------|
| `https://<cluster>.weaviate.cloud` | Weaviate Cloud | `WEAVIATE_API_KEY` is required |
| `http://localhost:8080` (or `127.0.0.1`) | Local (e.g. Docker) | API key optional; gRPC defaults to port `50051` |
| `https://weaviate.example.com`, `http://10.0.0.5:8080`, ... | Self-hosted / custom | API key optional; ports default to 443 (https) or 80 (http) for REST |

Optional variables for non-cloud servers:

| Variable | Default | Purpose |
|----------|---------|---------|
| `WEAVIATE_GRPC_PORT` | `50051` (`443` when gRPC is secure) | gRPC port, e.g. when Docker maps it elsewhere |
| `WEAVIATE_GRPC_HOST` | same as the URL host | gRPC host if it differs from REST (for example behind a proxy) |
| `WEAVIATE_GRPC_SECURE` | same as the URL scheme | `true` / `false` |

Examples:

```bash
# Local Docker with anonymous access
export WEAVIATE_URL="http://localhost:8080"

# Local Docker with a custom gRPC port and an API key
export WEAVIATE_URL="http://localhost:8080"
export WEAVIATE_GRPC_PORT=50052
export WEAVIATE_API_KEY="your-api-key"
```

Notes:

- Server-side streaming batches need Weaviate 1.36 or newer. `import.py` automatically falls back to client-side batching on older servers.
- `ask.py` uses the Weaviate Query Agent, which is only available on Weaviate Cloud.

## External Provider Env Vars and Headers

| Provider | Environment Variable(s) | Header(s) sent to Weaviate |
|----------|--------------------------|-----------------------------|
| Anthropic | `ANTHROPIC_API_KEY` | `X-Anthropic-Api-Key` |
| Anyscale | `ANYSCALE_API_KEY` | `X-Anyscale-Api-Key` |
| AWS | `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` | `X-Aws-Access-Key`, `X-Aws-Secret-Key` |
| Cohere | `COHERE_API_KEY` | `X-Cohere-Api-Key` |
| Databricks | `DATABRICKS_TOKEN` | `X-Databricks-Token` |
| Friendli | `FRIENDLI_TOKEN` | `X-Friendli-Api-Key` |
| Google Vertex AI | `VERTEX_API_KEY` | `X-Goog-Vertex-Api-Key` |
| Google AI Studio | `STUDIO_API_KEY` | `X-Goog-Studio-Api-Key` |
| HuggingFace | `HUGGINGFACE_API_KEY` | `X-HuggingFace-Api-Key` |
| Jina AI | `JINAAI_API_KEY` | `X-JinaAI-Api-Key` |
| Mistral | `MISTRAL_API_KEY` | `X-Mistral-Api-Key` |
| NVIDIA | `NVIDIA_API_KEY` | `X-Nvidia-Api-Key` |
| OpenAI | `OPENAI_API_KEY` | `X-OpenAI-Api-Key` |
| Azure OpenAI | `AZURE_API_KEY` | `X-Azure-Api-Key` |
| Voyage AI | `VOYAGE_API_KEY` | `X-Voyage-Api-Key` |
| xAI | `XAI_API_KEY` | `X-Xai-Api-Key` |

## Usage Notes

- Set only the provider keys your collection configuration actually uses.
- If multiple providers are configured, include all corresponding headers.
