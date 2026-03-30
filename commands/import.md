---
description: Import CSV, JSON, JSONL, or PDF files into a Weaviate collection
argument-hint: file [path] collection [name] mapping [json] tenant [name] skip-fields [fields] batch-size [100]
allowed-tools: Bash(uv:*), AskUserQuestion, Skill
---

# Import Data

Import one or more CSV, JSON, JSONL, or PDF files into a Weaviate collection with automatic type conversion. Multiple files of the same format can be passed in a single invocation.

## Usage

```
/weaviate:import file "data.csv" collection "CollectionName"
/weaviate:import file "data.csv" collection "CollectionName" mapping '{"src_col": "prop"}'
/weaviate:import file "document.pdf" collection "PDFDocuments"
/weaviate:import file "a.csv extra.jsonl" collection "CollectionName" skip-fields "id"
```

## Workflow

1. **CSV / JSON / JSONL** — collection must already exist. Create one first with `/weaviate:collections` if needed.
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py FILE --collection "CollectionName"
   ```

2. **PDF** — collection is created automatically on first run (multimodal schema with `ModernVBERT/colmodernvbert`); subsequent runs append to it.
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py FILE.pdf --collection "CollectionName"
   ```

3. **With mapping** (rename columns to match property names):
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py FILE --collection "CollectionName" \
     --mapping '{"old_col": "new_prop"}'
   ```

4. **Skip reserved fields** (`id`, `_additional` cause failures — drop or rename them):
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py FILE --collection "CollectionName" \
     --skip-fields "id"
   ```

5. **Multi-tenant collection:**
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py FILE --collection "CollectionName" \
     --tenant "tenant1"
   ```

6. **Multiple files — same format:**
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py a.csv b.csv c.csv \
     --collection "CollectionName"
   ```

7. **Multiple files — mixed formats** (CSV, JSON, and JSONL can be freely combined as long as their properties match the collection schema):
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py records.csv extra.jsonl patch.json \
     --collection "CollectionName"
   ```
   PDFs cannot be mixed with CSV/JSON/JSONL — import them in a separate run.

## Key Options

| Flag | Default | Description |
|------|---------|-------------|
| `--collection` / `-c` | required | Target collection name |
| `--mapping` / `-m` | — | JSON object mapping file columns/keys to property names |
| `--skip-fields` | — | Comma-separated field names to exclude (e.g. `id,created_at`) |
| `--tenant` / `-t` | — | Tenant name for multi-tenant collections |
| `--batch-size` / `-b` | `100` | Objects per batch |
| `--image-field` / `-i` | `doc_page` | BLOB property name for base64 page images (PDF only) |
| `--json` | `false` | Output results as JSON |

## Reserved Fields

`id` and `_additional` are reserved by Weaviate. If your data contains these, the import will fail. Always prefer renaming over dropping when the field contains meaningful data:

```bash
# Rename id to source_id
--mapping '{"id": "source_id"}'

# Drop id entirely
--skip-fields "id"
```

## PDF Requirements

Requires `poppler` on the system:
- macOS: `brew install poppler`
- Ubuntu/Debian: `sudo apt-get install poppler-utils`

## Environment

Requires:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication
