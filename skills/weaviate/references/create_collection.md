# Create Collection

Create a new Weaviate collection with a custom schema, optional vectorizer, and multi-tenancy support.

## Usage

```bash
uv run scripts/create_collection.py CollectionName --properties '[...]' [--description "..."] [--vectorizer "..."] [--replication-factor N] [--multi-tenancy] [--auto-tenant-creation] [--json]
```

## Parameters

| Parameter | Flag | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | — | Yes (positional) | — | Collection name (auto-capitalized per GraphQL convention) |
| `--properties` | `-p` | Yes | — | JSON array of property definitions |
| `--description` | `-d` | No | — | Collection description |
| `--vectorizer` | `-v` | No | `text2vec_weaviate` | Vectorizer module to use |
| `--replication-factor` | `-r` | No | — | Replication factor (defers to server default when not set) |
| `--multi-tenancy` | `-m` | No | `false` | Enable multi-tenancy for data isolation |
| `--auto-tenant-creation` | `-a` | No | `false` | Auto-create tenants on insert (requires `--multi-tenancy`) |
| `--json` | — | No | `false` | Output in JSON format |

## Property Definition Format

```json
{
  "name": "property_name",
  "data_type": "text",
  "description": "Optional description",
  "tokenization": "word",
  "nested_properties": []
}
```

- `name` (required): Property name
- `data_type` (required): One of the supported data types below
- `description` (optional): Human-readable description
- `tokenization` (optional): For text types — `word`, `lowercase`, `whitespace`, or `field`
- `nested_properties` (optional): For `object` / `object[]` types — array of nested property definitions

## Supported Data Types

`text`, `text[]`, `boolean`, `boolean[]`, `int`, `int[]`, `number`, `number[]`, `date`, `date[]`, `uuid`, `uuid[]`, `geoCoordinates`, `phoneNumber`, `blob`, `object`, `object[]`

Aliases: `bool` → `boolean`, `bool[]` → `boolean[]`

## Supported Vectorizers

`text2vec_weaviate`, `text2vec_openai`, `text2vec_cohere`, `text2vec_huggingface`, `text2vec_palm`, `text2vec_jinaai`, `text2vec_voyageai`, `text2vec_contextionary`, `text2vec_transformers`, `text2vec_gpt4all`, `text2vec_ollama`, `multi2vec_clip`, `multi2vec_bind`, `multi2vec_palm`, `img2vec_neural`, `ref2vec_centroid`, `none`

## Examples

Basic collection:

```bash
uv run scripts/create_collection.py Article \
  --properties '[{"name": "title", "data_type": "text"}, {"name": "body", "data_type": "text"}]'
```

Collection with various data types:

```bash
uv run scripts/create_collection.py Product \
  --properties '[
    {"name": "name", "data_type": "text"},
    {"name": "price", "data_type": "number"},
    {"name": "in_stock", "data_type": "boolean"},
    {"name": "tags", "data_type": "text[]"}
  ]'
```

With description and explicit vectorizer:

```bash
uv run scripts/create_collection.py Article \
  --description "News articles collection" \
  --properties '[{"name": "title", "data_type": "text"}]' \
  --vectorizer "text2vec_openai"
```

With multi-tenancy:

```bash
uv run scripts/create_collection.py Workspace \
  --properties '[{"name": "content", "data_type": "text"}]' \
  --multi-tenancy --auto-tenant-creation
```
