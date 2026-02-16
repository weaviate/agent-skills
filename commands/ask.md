---
description: Ask questions and get generated answers with sources (Query Agent ask mode)
argument-hint: query [question] collections [Collection1,Collection2]
allowed-tools: Bash(uv:*), AskUserQuestion, Skill
---

# Ask Weaviate (Query Agent Ask Mode)

Use Query Agent to ask questions and get generated answers with sources.

## Usage

```
/weaviate:ask query "your question" collections "Collection1,Collection2"
```

## Workflow

When necessary, use AskUserQuestion to make entering arguments easier.

1. Parse the query and collections arguments
2. If arguments are missing:
   - Run `/weaviate:collections` to list available collections
   - Use AskUserQuestion to prompt user to select
3. Run the Query Agent ask script:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/ask.py --query "USER_QUERY" --collections "COLLECTION_1,COLLECTION_2"
   ```
4. Display generated answer with sources

## Example

```
/weaviate:ask query "What are the key features of HNSW indexing?" collections "Documentation"
```

## For Raw Objects

Use `/weaviate:query` instead to get raw objects without generated answer.

## Environment

Requires:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication
