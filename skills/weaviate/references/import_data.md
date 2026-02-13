# Import Data

Import data from CSV, JSON, or JSONL files into an existing Weaviate collection with automatic type conversion and column mapping.

## Usage

```bash
uv run scripts/import.py "data.csv" --collection "CollectionName" [--mapping '{}'] [--tenant "name"] [--batch-size 100] [--json]
```

## Parameters

| Parameter | Flag | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | — | Yes (positional) | — | Path to CSV, JSON, or JSONL file |
| `--collection` | `-c` | Yes | — | Target collection name (must already exist) |
| `--mapping` | `-m` | No | — | JSON object mapping file columns/keys to collection properties |
| `--tenant` | `-t` | No | — | Tenant name for multi-tenant collections (required if collection has multi-tenancy enabled) |
| `--batch-size` | `-b` | No | `100` | Number of objects per batch |
| `--json` | — | No | `false` | Output in JSON format |

## File Formats

### CSV

- First row used as header (auto-detected via `csv.Sniffer`)
- Delimiter and quoting auto-detected
- Falls back to generated column names if no header detected
- Columns mapped to collection properties by name (case-sensitive)

### JSON

- Must be an array of objects: `[{"prop1": "value1"}, {"prop2": "value2"}]`
- Keys must match collection property names

### JSONL

- One JSON object per line
- Each object's keys must match collection property names

## Automatic Type Conversion

The import script automatically converts string values:

- `"true"` / `"false"` → boolean
- Digit strings → int
- Decimal strings → float
- `None` and empty strings are skipped

## Output

- **Default**: Import summary with total, imported, and failed counts (plus sample errors if any)
- **JSON**: Structured import stats

Returns exit code `1` if any imports fail.

## Examples

Import from CSV:

```bash
uv run scripts/import.py data.csv --collection "Articles"
```

Import with column mapping:

```bash
uv run scripts/import.py data.csv --collection "Articles" \
  --mapping '{"title_col": "title", "body_col": "content"}'
```

Import to multi-tenant collection:

```bash
uv run scripts/import.py data.jsonl --collection "Workspace" --tenant "tenant1"
```

Import JSON with custom batch size:

```bash
uv run scripts/import.py products.json --collection "Products" --batch-size 500
```

