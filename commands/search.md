---
description: Search a Weaviate collection using hybrid, semantic, or keyword search
argument-hint: query [search text] collection [name] type [hybrid|semantic|keyword] alpha [0.5] limit [10]
allowed-tools: Bash, AskUserQuestion, Skill
---

# Search Weaviate

Perform hybrid, semantic, or keyword search on a collection.

## Usage

```
/weaviate:search query "your query" collection "CollectionName" [type "hybrid"] [alpha "0.5"] [limit "10"]
```

## Workflow

When necessary, use AskUserQuestion to make entering arguments easier.

1. Parse arguments
2. If collection is missing:
   - Run `/weaviate:collections` to list available collections
   - Use AskUserQuestion to prompt user to select
3. If type is not specified, default to `hybrid`
4. Run the appropriate script based on type:

### Hybrid (default)
```bash
uv run skills/weaviate/scripts/hybrid_search.py --query "USER_QUERY" --collection "COLLECTION_NAME" --alpha 0.7 --limit 10 --json
```

### Semantic
```bash
uv run skills/weaviate/scripts/semantic_search.py --query "USER_QUERY" --collection "COLLECTION_NAME" --limit 10 --json
```

### Keyword
```bash
uv run skills/weaviate/scripts/keyword_search.py --query "USER_QUERY" --collection "COLLECTION_NAME" --limit 10 --json
```

## Examples

```
/weaviate:search query "machine learning" collection "Articles"
/weaviate:search query "SKU-12345" collection "Products" type "keyword"
/weaviate:search query "similar concepts" collection "Documents" type "semantic"
```

## Environment

Requires:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication
