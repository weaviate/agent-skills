# Ingestion, async indexing, and local Compose

## Batch API selection (Weaviate 1.36+ / Python 4.20+)

Server-side batching reached GA in Weaviate 1.36: the server paces the gRPC stream with backpressure instead of relying on client-chosen batch sizes.

| Python API | When to use it |
| --- | --- |
| `collection.data.ingest(iterable)` | One-shot streaming over an iterable/generator. Returns a result with `result.has_errors` and `result.errors` keyed by input index. |
| `collection.batch.stream()` | Context manager for incremental writes and live `batch.number_errors`. Read `collection.batch.failed_objects` right after the `with` block—it resets on the next batch. |
| `collection.batch.dynamic()` / `fixed_size()` | Fallback for servers < 1.36, clients < 4.20, or explicit client-side sizing/concurrency control. |
| `collection.batch.rate_limit()` | Client-side rate budget for rate-limited external embedding providers. |
| `collection.data.insert_many()` | Small materialized lists only; sends a single gRPC request (hits `GRPC_MAX_MESSAGE_SIZE` on large lists). |

- **Other SDKs:** TypeScript uses `collection.data.ingest(iterable)`; Go v6 uses `collection.Batch(ctx, ...)`. See [server-side batching docs](https://docs.weaviate.io/weaviate/manage-objects/import#server-side-batching).
- **Thread safety:** The Python [batch API is not thread-safe](https://docs.weaviate.io/weaviate/client-libraries/python/notes-best-practices); run one batch workflow at a time per client, or give concurrent workers separate clients.

## Streaming pre-embedded vectors

Pass a named vector dict (`{"body_vector": embedding}`)—never a bare vector list—on named-vector collections:

```python
from weaviate.classes.data import DataObject
from weaviate.util import generate_uuid5

objects = (
    DataObject(
        properties=props,
        uuid=generate_uuid5(props["article_key"]),  # unique per object, not parent doc ID
        vector={"body_vector": embedding},
    )
    for props, embedding in rows_with_vectors
)
result = articles.data.ingest(objects)
if result.errors:
    idx, err = next(iter(result.errors.items()))
    raise RuntimeError(f"{len(result.errors)} failed; row {idx}: {err.message}")
```

## Draining async vector indexing

With `ASYNC_INDEXING=true`, write completion and `/v1/.well-known/ready` do **not** mean vectors are indexed. This example assumes one node and one shard:

```python
import time

deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    nodes = client.cluster.nodes(collection="Article", output="verbose")
    shards = [s for n in nodes for s in (n.shards or []) if s.collection == "Article"]
    if len(nodes) == len(shards) == 1:
        shard = shards[0]
        if (
            shard.loaded is True
            and shard.vector_queue_length == 0
            and shard.vector_indexing_status == "READY"
        ):
            break
    time.sleep(1)
else:
    raise TimeoutError("Article vector indexing did not drain")
```

- For multiple shards or replicas, require a loaded, `READY`, zero-queue report for every expected `(node, shard)` pair. Missing reports and `per_node_status` do not establish queue length.

See [async indexing](https://docs.weaviate.io/weaviate/config-refs/indexing/vector-index#asynchronous-indexing), [monitoring](https://docs.weaviate.io/deploy/configuration/monitoring), and [multi-node shard status](https://docs.weaviate.io/weaviate/manage-collections/multi-node-setup).

## Local Docker Compose (1.40.7)

```yaml
services:
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.40.7
    command: ["--host", "0.0.0.0", "--port", "8080", "--scheme", "http"]
    ports:
      - "127.0.0.1:8080:8080"
      - "127.0.0.1:50051:50051"
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      AUTOSCHEMA_ENABLED: "false"
      PERSISTENCE_DATA_PATH: /var/lib/weaviate
      CLUSTER_HOSTNAME: node1
      ASYNC_INDEXING: "true"
      DEFAULT_QUANTIZATION: rq-8
      LIMIT_RESOURCES: "true"
    volumes:
      - data:/var/lib/weaviate
volumes:
  data:
```

- `DEFAULT_QUANTIZATION: rq-8` opts new HNSW indexes into RQ-8 (use `rq-4` on 1.40+ if testing 4-bit). `DEFAULT_VECTORIZER_MODULE` is ignored in 1.40.
- `LIMIT_RESOURCES: "true"` can override `GOMEMLIMIT`; both set soft Go runtime memory limits, not limits on sidecars or the OS page cache.
- For the Ollama baseline, add the `ollama` service and module settings from the [local quickstart](https://docs.weaviate.io/weaviate/quickstart/local) and pull the embedding model named in `SKILL.md`.
- For Transformers inference, add the [embedding](https://docs.weaviate.io/weaviate/model-providers/transformers/embeddings#configure-the-integration) or [reranker](https://docs.weaviate.io/weaviate/model-providers/transformers/reranker#configure-the-integration) sidecar, set `ENABLE_MODULES` + `TRANSFORMERS_INFERENCE_API` / `RERANKER_INFERENCE_API`, and configure the collection.

See [Docker installation](https://docs.weaviate.io/deploy/installation-guides/docker-installation) and the [environment variable reference](https://docs.weaviate.io/deploy/configuration/env-vars).
