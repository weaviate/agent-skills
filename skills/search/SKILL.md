---
name: search
description: Search Weaviate collections using hybrid, semantic (vector), or keyword (BM25) search. Use when performing direct searches without Query Agent.
---

# Weaviate Search

Direct search operations on Weaviate collections without using Query Agent.

## Environment Setup

Required environment variables:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication

## Search Types

### Hybrid Search (Default)

Combines vector and keyword search with configurable weighting:

```bash
uv run scripts/hybrid_search.py --query "your query" --collection "CollectionName" --alpha 0.7 --limit 10 --json
```

| Option | Description |
|--------|-------------|
| `--alpha` | Balance: 1.0=vector only, 0.0=keyword only (default: 0.7) |
| `--properties` | Comma-separated properties to search |
| `--target-vector` | Target vector name for named vector collections |

### Semantic Search

Vector similarity search using near_text:

```bash
uv run scripts/semantic_search.py --query "your query" --collection "CollectionName" --limit 10 --json
```

| Option | Description |
|--------|-------------|
| `--distance` | Maximum distance threshold |
| `--target-vector` | Target vector name for named vector collections |

### Keyword Search

BM25 keyword search for exact term matching:

```bash
uv run scripts/keyword_search.py --query "your query" --collection "CollectionName" --limit 10 --json
```

| Option | Description |
|--------|-------------|
| `--properties` | Properties to search with optional boost (e.g., `title^2,content`) |

## Common Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--query, -q` | Yes | Search query text |
| `--collection, -c` | Yes | Collection name |
| `--limit, -l` | No | Maximum results (default: 10) |
| `--json` | No | Output in JSON format |
