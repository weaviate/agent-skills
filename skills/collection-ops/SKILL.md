---
name: collection-ops
description: List and inspect Weaviate collections. Use when users need to see available collections, view collection schemas, or identify available properties for querying.
---

# Weaviate Collection Operations

Manage and inspect Weaviate collections.

## Environment Setup

Required environment variables:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication

## Operations

### List All Collections

Lists all collections in the Weaviate cluster with their descriptions and properties.

```bash
uv run scripts/list_collections.py [--json]
```

### Get Collection Details

Retrieves detailed configuration for a specific collection.

```bash
uv run scripts/get_collection.py --name "CollectionName" [--json]
```

## Output

### List Collections
Returns a table (or JSON) with:
- Collection Name
- Description
- Property list

### Collection Details
Returns:
- Collection name and description
- Vectorizer configuration
- Properties (name, data type, description)
- Replication and Multi-tenancy settings
