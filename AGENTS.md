# Weaviate Agent Skills - Setup Instructions

This document provides setup instructions for AI agents using the Weaviate skill and plugin.

## Prerequisites

### 1. Environment Variables

**Required:**
```bash
WEAVIATE_URL="https://your-cluster.weaviate.cloud"
WEAVIATE_API_KEY="your-api-key"
```

**Vectorizer API Keys (auto-detected):**

Set keys for providers your collections use. All are auto-detected from environment:

| Provider | Environment Variable |
|----------|---------------------|
| OpenAI | `OPENAI_API_KEY` |
| Cohere | `COHERE_API_KEY` |
| HuggingFace | `HUGGINGFACE_API_KEY` |
| Jina AI | `JINAAI_API_KEY` |
| Voyage AI | `VOYAGE_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| NVIDIA | `NVIDIA_API_KEY` |
| Google Vertex AI | `VERTEX_API_KEY` |
| Google AI Studio | `STUDIO_API_KEY` |
| Azure OpenAI | `AZURE_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Anyscale | `ANYSCALE_API_KEY` |
| Databricks | `DATABRICKS_TOKEN` |
| Friendli | `FRIENDLI_TOKEN` |
| xAI | `XAI_API_KEY` |
| AWS | `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` |

**Check if variables are set:**
```bash
[ -z "$WEAVIATE_URL" ] && echo "WEAVIATE_URL is NOT set" || echo "WEAVIATE_URL is set"
[ -z "$WEAVIATE_API_KEY" ] && echo "WEAVIATE_API_KEY is NOT set" || echo "WEAVIATE_API_KEY is set"
```

### 2. Python Runtime

All scripts require Python 3.11+.

```bash
python3 --version
```

### 3. uv Package Manager (Recommended)

Scripts use [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management.

**Check if uv is installed:**
```bash
uv --version
```

**Install uv if needed:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with Homebrew
brew install uv
```

## Running Scripts

All scripts are in `skills/weaviate/scripts/`. Run from that directory.

## Available Scripts

### Query Agent - Ask Mode
Generate AI-powered answers with source citations.

```bash
uv run scripts/ask.py --query "USER_QUERY" --collections "Collection1,Collection2" [--json]
```

**When to use:** User wants a direct answer to a question.

### Query Agent - Search Mode
Retrieve raw objects using natural language.

```bash
uv run scripts/query_search.py --query "USER_QUERY" --collections "Collection1,Collection2" [--limit 10] [--json]
```

**When to use:** User wants to explore/browse results across collections.

### Hybrid Search
Combines vector similarity and keyword matching.

```bash
uv run scripts/hybrid_search.py --query "USER_QUERY" --collection "CollectionName" [--alpha 0.7] [--limit 10] [--json]
```

Parameters:
- `--alpha`: Balance between vector (1.0) and keyword (0.0), default: 0.7
- `--properties`: Comma-separated properties to search
- `--target-vector`: Target vector name for named vectors

**When to use:** Default choice for most searches.

### Semantic Search
Pure vector similarity search.

```bash
uv run scripts/semantic_search.py --query "USER_QUERY" --collection "CollectionName" [--limit 10] [--distance 0.5] [--json]
```

Parameters:
- `--distance`: Maximum distance threshold
- `--target-vector`: Target vector name for named vectors

**When to use:** Finding conceptually similar content.

### Keyword Search
BM25 keyword matching.

```bash
uv run scripts/keyword_search.py --query "USER_QUERY" --collection "CollectionName" [--limit 10] [--json]
```

Parameters:
- `--properties`: Properties to search with optional boost (e.g., `title^2,content`)

**When to use:** Finding exact terms, IDs, or specific text.

### List Collections
Show all available collections.

```bash
uv run scripts/list_collections.py [--json]
```

**When to use:** Discovering what collections exist.

### Get Collection Details
Get configuration of a specific collection.

```bash
uv run scripts/get_collection.py --name "CollectionName" [--json]
```

**When to use:** Understanding collection schema and properties.

### Create Collection
Create a new Weaviate collection with custom properties.

```bash
uv run scripts/create_collection.py "CollectionName" --properties '[{"name": "property1", "data_type": "text"}]' [options]
```

Parameters:
- `name`: Collection name (positional argument, should start with uppercase)
- `--properties`: JSON array of property definitions (required)
- `--description`: Collection description
- `--vectorizer`: Vectorizer to use (e.g., `text2vec_openai`, `text2vec_cohere`, `none`)
- `--replication-factor`: Replication factor (default: 1)
- `--multi-tenancy`: Enable multi-tenancy for data isolation
- `--auto-tenant-creation`: Auto-create tenants on insert (requires `--multi-tenancy`)

**Property Definition Format:**
```json
{
  "name": "property_name",
  "data_type": "text",
  "description": "Optional description",
  "tokenization": "word"
}
```

**Supported Data Types:**
- `text`, `text[]`
- `boolean`, `boolean[]`
- `int`, `int[]`
- `number`, `number[]`
- `date`, `date[]`
- `uuid`, `uuid[]`
- `geoCoordinates`
- `phoneNumber`
- `blob`
- `object`, `object[]`

**Examples:**
```bash
# Basic collection
uv run scripts/create_collection.py "Article" \
  --properties '[{"name": "title", "data_type": "text"}, {"name": "body", "data_type": "text"}]'

# With multi-tenancy
uv run scripts/create_collection.py "MultiTenant" \
  --properties '[{"name": "content", "data_type": "text"}]' \
  --multi-tenancy --auto-tenant-creation

# With vectorizer
uv run scripts/create_collection.py "Article" \
--properties '[{"name": "title", "data_type": "text"}]' \
--vectorizer "text2vec_openai"
```

**When to use:** Creating new collections for organizing data.

## Workflow Recommendations

1. **Start by listing collections** if you don't know what's available:
   ```bash
   uv run scripts/list_collections.py
   ```

2. **Get collection details** to understand the schema:
   ```bash
   uv run scripts/get_collection.py --name "CollectionName"
   ```

3. **Choose the right search type:**
   - Direct answer needed → `ask.py`
   - Explore multiple collections → `query_search.py`
   - General search → `hybrid_search.py` (default)
   - Conceptual similarity → `semantic_search.py`
   - Exact terms/IDs → `keyword_search.py`

4. **Do not specify a vectorizer when creating collections** unless requested:
  ```bash
  uv run scripts/create_collection.py "Article" \
    --properties '[{"name": "title", "data_type": "text"}, {"name": "body", "data_type": "text"}]'
  ```

## Output Formats

All scripts support:
- **Markdown tables** (default): Human-readable
- **JSON** (`--json` flag): Machine-readable

## Error Handling

**Missing environment variables:**
```
Error: WEAVIATE_URL environment variable is not set
```
Solution: Ask us to set the required environment variables.

**Connection errors:**
```
WeaviateConnectionError: Failed to connect to Weaviate
```
Solution: Check WEAVIATE_URL and network connectivity.

**Collection not found:**
```
Error: Collection 'CollectionName' does not exist
```
Solution: Use `list_collections.py` to see available collections.

**Authentication error:**
```
Error: Vector search failed - authentication error
```
Solution: Set the appropriate vectorizer API key (e.g., `OPENAI_API_KEY`).

## Dependencies

All scripts use inline dependency declarations:

| Package | Version | Used By |
|---------|---------|---------|
| `weaviate-client` | >=4.19.2 | All scripts |
| `weaviate-agents` | >=1.2.0 | ask.py, query_search.py |
| `typer` | >=0.21.0 | All scripts |

With `uv run`, these are automatically installed.
