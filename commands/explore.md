---
description: Explore a Weaviate collection's data, including property metrics and sample objects
argument-hint: [name]
allowed-tools: Bash(uv:*), AskUserQuestion, Skill
---

# Weaviate Explore Collection

Explore data within a Weaviate collection, providing statistical metrics for properties and a sample of objects.

## Usage

```
/weaviate:explore "CollectionName"
/weaviate:explore "CollectionName" limit 5
```

## Workflow

1. Parse the collection name and optional limit arguments.
2. Run the explore collection script:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/explore_collection.py "COLLECTION_NAME" --limit 5
   ```
3. Display the results, including:
   - Total object count
   - Property metrics (count, min, max, mean, top occurrences, etc.)
   - Sample objects in a table format

## Examples

```
/weaviate:explore "Articles"
/weaviate:explore "Products" limit 10
```

## Environment

Requires:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication
