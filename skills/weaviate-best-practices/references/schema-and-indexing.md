# Schema and indexing (Weaviate-specific reference)

## Property tokenization and inverted index defaults

- `indexFilterable` and `indexSearchable` default to **`true`** on `TEXT`; `indexRangeFilters` defaults to **`false`** and only supports scalar `INT`, `NUMBER`, and `DATE` (not `*_ARRAY` types).
- When both `indexFilterable` and `indexRangeFilters` are enabled, Weaviate uses the range index for ordered comparisons (`<`, `<=`, `>`, `>=`) and `indexFilterable` for `==`/`!=`.
- Tokenization affects **both** BM25 and equality filters:
  - `Tokenization.FIELD`: whole-string exact match (IDs, SKUs, categories, statuses). Pair with `index_searchable=False` if not BM25-searched.
  - `Tokenization.WORD`: default for prose.
  - `Tokenization.LOWERCASE`: preserves punctuation (e.g. hyphenated codes) in BM25/filters.
- Disable both `index_filterable=False` and `index_searchable=False` on display-only or vector-only properties (a property can still feed `source_properties` without inverted indexes).

See [inverted index config](https://docs.weaviate.io/weaviate/config-refs/indexing/inverted-index) and [tokenization](https://docs.weaviate.io/weaviate/concepts/indexing/inverted-index).

## Vectorizer configuration (1.40 breaking change)

- Weaviate 1.40 [ignores `DEFAULT_VECTORIZER_MODULE`](https://weaviate.io/blog/weaviate-1-40-release#vector-configuration-defaults-breaking-change). Always set `vector_config=Configure.Vectors.*(...)` per collection.
- **Pre-embedded docs + managed query vectorization:** Configure the compatible managed vectorizer on the named vector and pass precomputed document vectors under that same vector name on write (`vector={"body_vector": vec}`). Verify query/passage prefix compatibility for asymmetric models. If mixing body-only precomputed vectors with managed Transformers writes, set `vectorize_collection_name=False`; `source_properties` alone leaves the collection-name prefix enabled by default.

## Vector indexes, quantization, and Cloud defaults

```python
from weaviate.classes.config import Configure, VectorFilterStrategy

hnsw_rq8 = Configure.VectorIndex.hnsw(quantizer=Configure.VectorIndex.Quantizer.rq(bits=8))
hnsw_rq4 = Configure.VectorIndex.hnsw(quantizer=Configure.VectorIndex.Quantizer.rq(bits=4))
hnsw_pathseer = Configure.VectorIndex.hnsw(filter_strategy=VectorFilterStrategy.PATHSEER)
disk_index = Configure.VectorIndex.hfresh()
```

Pass the chosen index as `vector_index_config` inside `Configure.Vectors.*(...)`.

| Index / Option | Weaviate-specific details |
| --- | --- |
| `hfresh` | GA for single vectors since [1.38](https://weaviate.io/blog/weaviate-1-38-release#hfresh-vector-index---general-availability) (multi-vector via MUVERA in 1.40). Disk postings with mandatory 1-bit RQ; centroid index uses 8-bit RQ. Supports cosine or squared L2. |
| `rq(bits=8)` / `rq(bits=4)` | Rotational Quantization needs no training step. RQ-4 is HNSW-only and GA in [1.40](https://weaviate.io/blog/weaviate-1-40-release#4-bit-rotational-quantization---general-availability). Once enabled, quantization cannot be disabled in place, and RQ bit width cannot change. |
| `dynamic` | Starts `flat`, switches to `hnsw` at a threshold. Experimental; requires `ASYNC_INDEXING=true`. |
| `filter_strategy` | HNSW defaults to `ACORN` (since 1.34). `VectorFilterStrategy.PATHSEER` (new in [1.40](https://weaviate.io/blog/pathseer-filtered-vector-search)) adapts filter-first vs distance-first per node and can be switched without reindexing. `SWEEPING` is also available. |

- **Defaults differ by deployment:** Self-hosted `DEFAULT_QUANTIZATION` defaults to `none` (explicit collection quantization overrides it). Weaviate Cloud Free tier allows [one collection](https://docs.weaviate.io/cloud/manage-clusters/default-settings) and enforces [Cost Optimized (HFresh)](https://docs.weaviate.io/cloud/manage-clusters/create).

See [RQ compression](https://docs.weaviate.io/weaviate/configuration/compression/rq-compression), [vector index options](https://docs.weaviate.io/weaviate/config-refs/indexing/vector-index), and [filtering strategies](https://docs.weaviate.io/weaviate/concepts/filtering).

## Schema evolution, Object TTL, aliases, and multi-tenancy

- **In-place index drops:** You can drop unused inverted indexes (`searchable`, `filterable`, `rangeFilters`) in place without rebuilding the collection (GA 1.36: `collection.config.delete_property_index("title", "searchable")`). Dropping a named vector via `delete_vector_index(name)` (1.40 / Python 4.24+) irreversibly deletes its index **and stored embeddings** in the background. Wait for the name to disappear from `vector_config` before reusing it. Adding a named vector does **not** backfill existing objects.
- **Native Object TTL (GA 1.36):** Configure automatic expiration at collection creation via `object_ttl_config=Configure.ObjectTTL.*(...)` (by creation time, update time, or a `DATE` property, with optional `filter_expired_objects=True`); requires `OBJECTS_TTL_DELETE_SCHEDULE` on the server.
- **Aliases (GA 1.33):** For incompatible schema changes, backfill a new collection and swap a [collection alias](https://docs.weaviate.io/weaviate/manage-collections/collection-aliases). On 1.40.7, [runtime property reindex](https://github.com/weaviate/weaviate/blob/v1.40.7/docs/runtime-reindex.md#2-rest-surface) can change text tokenization in place when `RUNTIME_REINDEX_ENABLED=true` (off by default). Use aliases for queries/object access, not schema admin:

```python
client.alias.update(alias_name="Products", new_target_collection="ProductV2")
```

- **Multi-tenancy:** For isolated subsets with identical schemas, use [multi-tenancy](https://docs.weaviate.io/weaviate/best-practices#use-multi-tenancy-for-data-subsets) rather than one collection per subset.
