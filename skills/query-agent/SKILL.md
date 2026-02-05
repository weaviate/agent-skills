---
name: query-agent
description: Query Weaviate using natural language with Query Agent. Supports search mode (returns objects for agent processing) and ask mode (returns generated answers with sources). Use when user wants to search Weaviate collections with natural language queries.
---

# Weaviate Query Agent

Query Agent translates natural language into precise Weaviate database operations.

## Environment Setup

Required environment variables:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication

## Modes

### Search Mode (Default)
Returns objects for agent/pipeline processing:

```bash
uv run scripts/search.py --query "USER_QUERY" --collections "Collection1,Collection2" --json
```

### Ask Mode
Returns generated answer with sources:

```bash
uv run scripts/ask.py --query "USER_QUERY" --collections "Collection1,Collection2"
```

## When to Use Each Mode

| Mode | Use When |
|------|----------|
| **Search** | Higher-level agent will process results, need raw objects |
| **Ask** | User wants direct answer with source citations |

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--query, -q` | Yes | Natural language query |
| `--collections, -c` | Yes | Comma-separated collection names |
| `--json` | No | Output in JSON format |
