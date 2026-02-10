---
description: Fetch and filter objects from Weaviate collections
argument-hint: collection [name] filters [json] limit [10] id [uuid]
allowed-tools: Bash(uv:*), AskUserQuestion, Skill
---

# Fetch and Filter Objects

Fetch specific objects by ID or filter them using complex logic (AND/OR). Always use this command after exploring the collection using `/weaviate:explore` command.

## Usage

```
/weaviate:fetch collection "CollectionName" filters '{"property": "prop", "operator": "equal", "value": "val"}'
/weaviate:fetch collection "CollectionName" id "UUID"
```

## Workflow

1.  **Fetch by ID:**
    ```bash
    uv run skills/weaviate/scripts/fetch_filter.py "COLLECTION_NAME" --id "UUID" --json
    ```

2.  **Fetch with Filters:**
    ```bash
    uv run skills/weaviate/scripts/fetch_filter.py "COLLECTION_NAME" --filters 'JSON_STRING' --limit 10 --json
    ```

### Filter Syntax

Filters must be a JSON string.

**Simple Filter:**
```json
[{"property": "category", "operator": "equal", "value": "Science"}]
```

**OR Logic:**
```json
{
  "operator": "or",
  "filters": [
    {"property": "word_count", "operator": "greater_than", "value": 1000},
    {"property": "title", "operator": "like", "value": "*Research*"}
  ]
}
```

**Complex Nesting:**
```json
{
  "operator": "and",
  "filters": [
    {"property": "is_published", "operator": "equal", "value": true},
    {
      "operator": "or", 
      "filters": [
        {"property": "author", "operator": "equal", "value": "Jane Doe"},
        {"property": "views", "operator": "greater_than", "value": 5000}
      ]
    }
  ]
}
```

## Operators

-   `equal`, `not_equal`
-   `less_than`, `less_or_equal`
-   `greater_than`, `greater_or_equal`
-   `like` (use `*` for wildcards)
-   `contains_any`, `contains_all` (value must be a list)
-   `is_none` (value must be boolean)

## Environment

Requires:
-   `WEAVIATE_URL`: Weaviate Cloud cluster URL
-   `WEAVIATE_API_KEY`: API key for authentication
