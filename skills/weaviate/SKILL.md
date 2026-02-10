---
name: weaviate
description: Search, query, and manage Weaviate vector database collections. Use for semantic search, hybrid search, keyword search, natural language queries with AI-generated answers, and collection inspection.
---

# Weaviate Database Operations

This skill provides comprehensive access to Weaviate vector databases including search operations, natural language queries, and schema inspection.

## Environment Variables

**Required:**
- `WEAVIATE_URL` - Your Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY` - Your Weaviate API key

**Vectorizer API Keys (auto-detected):**
Set keys for providers your collections use. All are auto-detected from environment:
- `OPENAI_API_KEY`, `COHERE_API_KEY`, `HUGGINGFACE_API_KEY`
- `JINAAI_API_KEY`, `VOYAGE_API_KEY`, `MISTRAL_API_KEY`
- `NVIDIA_API_KEY`, `VERTEX_API_KEY`, `STUDIO_API_KEY`
- `AZURE_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`
- `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`

## Available Scripts

### Query Agent - Ask Mode
Generate AI-powered answers with source citations.

```bash
uv run scripts/ask.py --query "USER_QUESTION" --collections "COLLECTION_1,COLLECTION_2" [--json]
```

**When to use:** User wants a direct answer to a question based on collection data.

### Query Agent - Search Mode
Retrieve raw objects using natural language queries across multiple collections.

```bash
uv run scripts/query_search.py --query "USER_QUERY" --collections "COLLECTION_1,COLLECTION_2" [--limit 10] [--json]
```

**When to use:** User wants to explore/browse results across collections.

### Hybrid Search
Combines vector similarity and keyword matching (best default choice).

```bash
uv run scripts/hybrid_search.py --query "USER_QUERY" --collection "COLLECTION_NAME" [--alpha 0.7] [--limit 10] [--json]
```

Parameters:
- `--alpha`: Balance between vector (1.0) and keyword (0.0), default: 0.7
- `--properties`: Comma-separated properties to search
- `--target-vector`: Target vector name for named vectors

**When to use:** Default for most searches. Good balance of semantic understanding and exact matching.

### Semantic Search
Pure vector similarity search using embeddings.

```bash
uv run scripts/semantic_search.py --query "USER_QUERY" --collection "COLLECTION_NAME" [--limit 10] [--distance 0.5] [--json]
```

Parameters:
- `--distance`: Maximum distance threshold
- `--target-vector`: Target vector name for named vectors

**When to use:** Finding conceptually similar content regardless of exact wording.

### Keyword Search
BM25 keyword matching for exact term searches.

```bash
uv run scripts/keyword_search.py --query "USER_QUERY" --collection "COLLECTION_NAME" [--limit 10] [--json]
```

Parameters:
- `--properties`: Properties to search with optional boost (e.g., `title^2,content`)

**When to use:** Finding exact terms, IDs, SKUs, or specific text patterns.

### List Collections
Show all available collections with their properties.

```bash
uv run scripts/list_collections.py [--json]
```

**When to use:** Discovering what collections exist before searching.

### Get Collection Details
Get detailed configuration of a specific collection.

```bash
uv run scripts/get_collection.py --name "COLLECTION_NAME" [--json]
```

**When to use:** Understanding collection schema, vectorizer config, and properties.

### Create Collection
Create a new Weaviate collection with custom schema.

```bash
uv run scripts/create_collection.py "CollectionName" --properties '[...]' [--description "..."] [--vectorizer "..."] [--json]
```

Parameters:
- `name`: Collection name (positional argument, will be capitalized per GraphQL convention)
- `--properties`: JSON array of property definitions (see examples below)
- `--description`: Optional collection description
- `--vectorizer`: Optional vectorizer (e.g., `text2vec_openai`, `text2vec_cohere`, `none`)
- `--replication-factor`: Optional replication factor (default: 1)
- `--multi-tenancy`: Enable multi-tenancy for data isolation (each tenant on separate shard)
- `--auto-tenant-creation`: Auto-create tenants on insert (requires `--multi-tenancy`)

**Supported Data Types:**
`text`, `text[]`, `boolean`, `boolean[]`, `int`, `int[]`, `number`, `number[]`, `date`, `date[]`, `uuid`, `uuid[]`, `geoCoordinates`, `phoneNumber`, `blob`, `object`, `object[]`

**Property Definition Format:**
```json
{
  "name": "property_name",
  "data_type": "text",
  "description": "Optional description",
  "tokenization": "word",  // Optional for text types: word, lowercase, whitespace, field
  "nested_properties": []  // Optional for object types
}
```

**Examples:**

Basic collection with text properties:
```bash
uv run scripts/create_collection.py "Article" \
  --properties '[{"name": "title", "data_type": "text"}, {"name": "body", "data_type": "text"}]'
```

Collection with various data types:
```bash
uv run scripts/create_collection.py "Product" \
  --properties '[
    {"name": "name", "data_type": "text"},
    {"name": "price", "data_type": "number"},
    {"name": "in_stock", "data_type": "boolean"},
    {"name": "tags", "data_type": "text[]"}
  ]'
```

Collection with vectorizer and description:
```bash
uv run scripts/create_collection.py "Article" \
  --description "News articles collection" \
  --properties '[{"name": "title", "data_type": "text"}]' \
  --vectorizer "text2vec_openai"
```

**When to use:** Creating new collections with custom schemas before importing data.

## Workflow Recommendations

1. **Start by listing collections** if you don't know what's available:
   ```bash
   uv run scripts/list_collections.py
   ```

2. **Get collection details** to understand the schema:
   ```bash
   uv run scripts/get_collection.py --name "COLLECTION_NAME"
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
- **Markdown tables** (default): Human-readable output
- **JSON** (`--json` flag): Machine-readable for further processing

## Error Handling

Common errors:
- `WEAVIATE_URL not set` → Set the environment variable
- `Collection not found` → Use `list_collections.py` to see available collections
- `Authentication error` → Check API keys for both Weaviate and vectorizer providers
