# Search, async client, and RAG idioms (Weaviate-specific reference)

## Async Python client

```python
import weaviate


async def sample_products():
    async with weaviate.use_async_with_local() as client:
        products = client.collections.use("Product")
        return (await products.query.fetch_objects(limit=5)).objects
```

If HTTP succeeds but gRPC times out, check the gRPC host/port (`50051` by default locally) and proxy routing before raising timeouts. See [async Python client](https://docs.weaviate.io/weaviate/client-libraries/python/async) and [client notes](https://docs.weaviate.io/weaviate/client-libraries/python/notes-best-practices).

## 1.38+ search features and built-in MCP

- **Built-in MCP server (GA [1.38](https://weaviate.io/blog/weaviate-1-38-release)):** Set `MCP_SERVER_ENABLED=true` to serve `/v1/mcp` over Streamable HTTP. MCP uses the instance's authentication and authorization settings; enabling it does not secure an anonymous deployment. Leave `MCP_SERVER_WRITE_ACCESS_ENABLED` off unless clients need writes.
- **Boost (GA 1.39):** Use [Boost](https://weaviate.io/blog/weaviate-1-39-release#boost-api---general-availability) for soft ranking preferences (e.g. freshness) without a model call—not for hard filters.
- **MMR (GA 1.39):** Use MMR for near-duplicate diversity on **unpaginated** retrieval (`limit` sets candidates, MMR limit sets returned items). Do not combine with offset pagination.

## Hybrid weights and score explanations

```python
from weaviate.classes.query import Filter, MetadataQuery

eligible = Filter.by_property("available").equal(True) & Filter.by_property(
    "price_cents"
).less_or_equal(7000)
page = products.query.hybrid(
    "waterproof walking shoes",
    target_vector="description_vector",
    query_properties=["name^2", "description"],
    filters=eligible,
    limit=10,
    offset=0,
    return_metadata=MetadataQuery(score=True, explain_score=True),
)
```

- On replicated collections, choose the [read or write consistency level](https://docs.weaviate.io/weaviate/concepts/replication-architecture/consistency) with `collection.with_consistency_level(...)`. `ONE`, `QUORUM`, and `ALL` determine how many replicas must respond. A stronger read level affects the object versions returned, not which UUIDs a search matches.
- A filter-only count is not a hybrid hit count. Avoid exact counts on every page.
- `offset + limit` cannot exceed `QUERY_MAXIMUM_RESULTS`. For full collection scans/exports, use [cursor iteration](https://docs.weaviate.io/weaviate/manage-objects/read-all-objects) (`collection.iterator()`), not ranked `offset`/`limit`.
- See [filters](https://docs.weaviate.io/weaviate/search/filters), [hybrid search](https://docs.weaviate.io/weaviate/search/hybrid), and [pagination](https://docs.weaviate.io/weaviate/search/basics#paginate-with-limit-and-offset).

## Local reranker and integrated generation

- **Local reranker:** Enable `reranker-transformers` on the server and set `RERANKER_INFERENCE_API` to the [sidecar URL](https://docs.weaviate.io/weaviate/model-providers/transformers/reranker). Then configure `reranker_config=Configure.Reranker.transformers()` (or `Reconfigure.Reranker.transformers()` via `collection.config.update()`). Pass `rerank=Rerank(prop="body", query=question)` on the bounded RAG query only.
- **Integrated generation:** Use Weaviate's grouped task for one answer synthesized across retrieved objects. For the [local Ollama integration](https://docs.weaviate.io/weaviate/model-providers/ollama/generative), pull the generation model and pass its tag as `model` in `Configure.Generative.ollama(...)` or `Reconfigure.Generative.ollama(...)`. For example, [`gemma4:12b`](https://ollama.com/library/gemma4:12b) runs on [Ollama 0.30.3 or later](https://github.com/ollama/ollama/releases/tag/v0.30.3). In Compose, set `api_endpoint="http://ollama:11434"` if `ollama` is the service name; the default `localhost` points to the Weaviate container.

See [reranking](https://docs.weaviate.io/weaviate/search/rerank) and [generative search](https://docs.weaviate.io/weaviate/search/generative).
