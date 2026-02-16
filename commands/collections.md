---
description: List all collections in Weaviate or get the schema of an individual collection
argument-hint: [name]
allowed-tools: Bash(uv:*), AskUserQuestion, Skill
---

# Weaviate Collections

List all Weaviate collections or get detailed schema information for a specific collection.

## Usage

```
/weaviate:collections
/weaviate:collections name "CollectionName"
```

## Workflow

### List All Collections

When no arguments are provided:

1. Run the list collections script:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/list_collections.py
   ```
2. Display collection names with descriptions and properties

### Get Collection Schema

When a collection name is provided:

1. Parse the name argument
2. Run the get collection script:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/get_collection.py --name "COLLECTION_NAME"
   ```
3. Display detailed schema including:
   - Description
   - Vectorizer configuration
   - Properties with data types
   - Replication settings
   - Multi-tenancy status

## Examples

```
/weaviate:collections
/weaviate:collections name "Articles"
```

## Environment

Requires:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication