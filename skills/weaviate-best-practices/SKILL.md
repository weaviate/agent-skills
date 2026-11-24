---
name: weaviate-best-practices
description: Use when building, migrating, reviewing, or scaling any Weaviate app or service (Docker Compose, Weaviate Cloud, `weaviate-client`, `vector_config`, quantization/RQ/HFresh, bulk batch ingestion, async indexing, hybrid/filtered search, reranking, or RAG). Not for live-cluster administration or ad-hoc data queries.
---

# Weaviate application best practices

- **Last updated:** 2026-11-24 · **Target versions:** Weaviate `1.40.7`, `weaviate-client==4.24.1`

Focuses on current Weaviate APIs, defaults, and best practice understanding of how to get the most out of Weaviate. Examples use Python v4 with no Cloud or model-provider credentials. Load references only as needed:
- [references/schema-and-indexing.md](references/schema-and-indexing.md): tokenizers, index defaults, HFresh/RQ-4/RQ-8, Cloud Free limits, ACORN vs PathSeer, Object TTL, schema/index drops, collection aliases
- [references/ingestion-and-async.md](references/ingestion-and-async.md): server-side batching (`data.ingest` / `batch.stream`), pre-embedded vectors, async queue drain, pinned 1.40.7 Compose & `LIMIT_RESOURCES`
- [references/search-and-idioms.md](references/search-and-idioms.md): async client, built-in MCP (1.38), Boost & MMR (1.39), `explain_score`, cursors, local reranker/Ollama

**Not covered here:** Cluster/ops configuration—including RBAC, OIDC/API-key user management, replication, backups, and cluster monitoring. Weaviate supports native RBAC and OIDC; consult the [deployment & configuration docs](https://docs.weaviate.io/deploy) or [Hosted Docs MCP](https://docs.weaviate.io/weaviate/mcp/docs-mcp-server) when you need them.

## 1. Versions and transports

- **Versions:** Check existing pins before choosing APIs. For new deployments, pin the latest **stable** server and a compatible SDK from the [release matrix](https://docs.weaviate.io/weaviate/release-notes#weaviate-database-and-client-releases). The examples use the target versions above. Use [Hosted Docs MCP](https://docs.weaviate.io/weaviate/mcp/docs-mcp-server) when available.
- **SDK connectivity:** Make both HTTP and gRPC endpoints reachable for SDK workflows. Self-hosted defaults are `8080` and `50051`; managed endpoints can differ. Do not add new GraphQL queries: the API is [deprecated and scheduled for removal](https://docs.weaviate.io/weaviate/api/graphql). Use SDK queries over gRPC. If gRPC is unavailable, check whether [REST Search supports the operation](https://docs.weaviate.io/weaviate/api/graphql/migration#rest-search-api).

In Python, `collections.use("Article")` returns a lazy handle; use `collections.exists("Article")` to check existence. Run the later snippets inside an open client context:

```python
import weaviate

with weaviate.connect_to_local() as client:
    articles = client.collections.use("Article")
```

## 2. Schema, named vectors, and index defaults

- **Breaking in 1.40:** The server ignores `DEFAULT_VECTORIZER_MODULE`. Always configure vectors per collection via `vector_config=Configure.Vectors.*(...)`—never legacy `vectorizer_config` / `Configure.Vectorizer`.
- **Server & property defaults:** Set `AUTOSCHEMA_ENABLED=false`. On `DataType.TEXT`, `index_filterable` and `index_searchable` default to `True`: use `tokenization=Tokenization.FIELD` for whole-value filters and set `index_searchable=False` only if the field is not used by BM25. `index_range_filters` defaults to **`False`**—explicitly set `index_range_filters=True` on scalar `INT`/`NUMBER`/`DATE` properties used in range filters.
- **Local baseline:** This example follows the [Docker quickstart](https://docs.weaviate.io/weaviate/quickstart/local) and uses Ollama with `nomic-embed-text` for embeddings. Other [model integrations](https://docs.weaviate.io/weaviate/model-providers) are available.

```python
from weaviate.classes.config import Configure, DataType, Property, Tokenization

client.collections.create(
    "Article",
    vector_config=Configure.Vectors.text2vec_ollama(
        name="body_vector",
        api_endpoint="http://ollama:11434",
        model="nomic-embed-text",
        source_properties=["body"],
        vector_index_config=Configure.VectorIndex.hnsw(
            quantizer=Configure.VectorIndex.Quantizer.rq(bits=8),
        ),
    ),
    properties=[
        Property(name="body", data_type=DataType.TEXT),
        Property(
            name="article_key",
            data_type=DataType.TEXT,
            tokenization=Tokenization.FIELD,
            index_searchable=False,
        ),
        Property(
            name="category",
            data_type=DataType.TEXT,
            tokenization=Tokenization.FIELD,
            index_searchable=False,
        ),
        Property(name="created_at", data_type=DataType.DATE, index_range_filters=True),
    ],
)
```

## 3. Vector index, quantization, and filtered HNSW (1.34–1.40)

- **Indexes:** `Flat` for small collections/tenants; `HNSW` for fast in-RAM reads; **`HFresh`** (GA 1.38, disk postings + 1-bit RQ + 8-bit RQ centroids) when RAM is constrained and SSD I/O is available.
- **Quantization:** Start larger HNSW collections on **RQ-8** (shown above); test **RQ-4** (GA 1.40, HNSW only) on a separate index because RQ bit width cannot change in place. Self-hosted `DEFAULT_QUANTIZATION` defaults to `none`; Weaviate Cloud Free tier enforces 1 collection and HFresh.
- **Filtered HNSW:** **`ACORN`** is the default since 1.34. On 1.40+, benchmark **`PathSeer`** (`VectorFilterStrategy.PATHSEER`, switchable without reindexing) for heavy or low-selectivity filtered workloads.

## 4. Server-side batching and async indexing (1.36+ / Python 4.20+)

- **Server-side batching (GA 1.36, Python 4.20+):** Prefer `collection.data.ingest(iterable)` (one-shot, inspect `result.errors`) or `collection.batch.stream()` (context manager, check `batch.number_errors` and `collection.batch.failed_objects` immediately after exit—resets on next batch) over legacy client-side `batch.dynamic()`/`fixed_size()`. Python's batch API is **not thread-safe** per client.
- **UUIDs & pre-embedded vectors:** Derive UUIDv5 from a unique per-object key (never a shared parent document ID). Pass pre-embedded vectors as a named dict (`vector={"body_vector": vec}`).
- **Async indexing:** With `ASYNC_INDEXING=true`, wait for [every expected shard replica](references/ingestion-and-async.md#draining-async-vector-indexing) to report loaded, `READY`, and an empty vector queue. Missing reports do not establish readiness.

```python
from weaviate.util import generate_uuid5

with articles.batch.stream() as batch:
    for row in rows:
        batch.add_object(
            properties=row,
            uuid=generate_uuid5(row["article_key"]),
            # vector={"body_vector": vec},  # named dict for pre-embedded rows
        )

failed = articles.batch.failed_objects
if failed:
    raise RuntimeError(f"{len(failed)} writes failed: {failed[0].message}")
```

## 5. Hybrid search, reranking, and RAG

- **Hybrid:** Use `.query.hybrid(..., target_vector="body_vector", filters=eligible)` for mixed keyword/semantic search. For `self_provided` vectors, pass `vector=query_embedding` and keep the text `query` for BM25. Keep shallow `offset`/`limit` pagination (bounded by `QUERY_MAXIMUM_RESULTS`) separate from bounded RAG retrieval + `Rerank(...)` (never rerank or apply MMR per page).
- **Ranking:** Use **Boost** (GA 1.39) for soft preferences and **MMR** (GA 1.39) for unpaginated diversity.
- **Mutable reranker/generative configs:** Configure at creation (`Configure.Reranker.*` / `Configure.Generative.*`) or update in place via `collection.config.update(...)`, provided the module is enabled on the server (`ENABLE_MODULES`).

```python
from weaviate.classes.config import Reconfigure
from weaviate.classes.query import Filter, Rerank

eligible = Filter.by_property("category").equal("guides")
page = articles.query.hybrid(
    text, target_vector="body_vector", filters=eligible, limit=10, offset=20
)

# Requires reranker-transformers and a reachable RERANKER_INFERENCE_API:
articles.config.update(
    reranker_config=Reconfigure.Reranker.transformers(),
)
passages = articles.query.hybrid(
    question,
    target_vector="body_vector",
    filters=eligible,
    limit=20,
    rerank=Rerank(prop="body", query=question),
).objects[:6]
```
