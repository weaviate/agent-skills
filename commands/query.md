---
description: Query Weaviate using natural language (Query Agent search mode)
argument-hint: query [search text] collections [Collection1,Collection2] limit [10]
allowed-tools: Bash(uv:*), AskUserQuestion, Skill
---

# Query Weaviate (Search Mode)

Use Query Agent to search Weaviate collections with natural language. Returns objects for further processing.

## Usage

```
/weaviate:query query "your search query" collections "Collection1,Collection2" limit 10
```

## Workflow

When necessary, use AskUserQuestion to make entering arguments easier.

1. Parse the query, collections, and limit arguments
2. If arguments are missing:
   - Run `/weaviate:collections` to list available collections
   - Use AskUserQuestion to prompt user to select
   - Default limit to 10 if not specified
3. Run the Query Agent search script:
   ```bash
   uv run skills/weaviate/scripts/query_search.py --query "USER_QUERY" --collections "COLLECTION_1,COLLECTION_2" --limit "LIMIT" --json
   ```
4. Display results to user

## Example

```
/weaviate:query query "articles about vector databases" collections "Articles,BlogPosts" limit 5
```

## For Generated Answers

Use `/weaviate:ask` instead to get generated answers with sources.

## Environment

Requires:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication
