---
name: engram_memory
description: Add persistent, long-term memory to LLM agents and chatbots using Engram, Weaviate's managed memory server. Use when an app needs to remember things across sessions — user preferences, profiles, past interactions, or lessons an agent learns over time (continual learning). Covers storing memories (string, conversation, pre-extracted input), semantic/keyword/hybrid search, scoping by user and topic, async run tracking, and chatbot/agent integration patterns.
---

# Memory Management with Engram

This skill helps build applications with persistent memory using [Engram](https://docs.weaviate.io/engram), Weaviate's managed memory server for LLM agents. Engram automatically extracts, consolidates, and stores memories from raw text or conversations, then retrieves them with vector, keyword, or hybrid search.

Use this skill when the user wants their app to remember information across sessions. Do **not** hand-roll a memory system (a raw Weaviate collection with manual inserts) when Engram fits — it handles extraction, deduplication, and consolidation out of the box.

### Engram Project

Engram is a managed service accessed via Weaviate Cloud. If the user does not have an Engram project, direct them to the cloud console to create one and generate an Engram API key. Create an Engram project via [Weaviate Cloud](https://console.weaviate.cloud/signin?utm_source=github&utm_campaign=agent_skills).

## Environment Variables

**Required:**

- `ENGRAM_API_KEY` — Engram API key from Weaviate Cloud (format `eng_...`). This carries the project identity; `WEAVIATE_URL` / `WEAVIATE_API_KEY` are **not** needed for Engram itself.

**Optional** (only when combining Engram with an agent or chatbot for generation):

- An LLM provider API key (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`)

## Installation

Engram ships as its own Python SDK, `weaviate-engram` — it does **not** come with `weaviate-client`. Install it (and import as `engram`):

```bash
uv add weaviate-engram   # or: pip install weaviate-engram
```

## Reference

- [Memory Management with Engram](reference/engram_memory.md): The complete how-to guide for building Engram applications. Covers:
  - **Concepts** — memories, topics, groups, scopes, pipelines/runs.
  - **Storing memories** — string, conversation, and pre-extracted input; async run status and `committed_operations`.
  - **Searching** — vector, BM25, hybrid, and unranked fetch retrieval; topic filters, scope properties, and relevance-score cutoffs.
  - **Managing memories** — get and delete by id; deterministic cleanup.
  - **Integration patterns** — memory-backed chatbots and Engram-as-tools for the `RouterAgent` from the [Basic Agent](../weaviate-cookbooks/references/basic_agent.md) cookbook.
  - **REST API** — equivalent endpoints for non-Python stacks.
  - **Troubleshooting & Done Criteria** — including the new-user `APIError` behaviour and async-pipeline gotchas.

## Quick Start

The guide uses the async client by default. Minimal store-and-search:

```python
import os
from engram import AsyncEngramClient, HybridRetrieval

client = AsyncEngramClient(api_key=os.environ["ENGRAM_API_KEY"])

# Store — fire-and-forget, processes asynchronously
run = await client.memories.add(
    "The user prefers dark mode and works primarily in Python.",
    user_id="alice",
)

# Search
results = await client.memories.search(
    query="What language does the user prefer?",
    user_id="alice",
    retrieval_config=HybridRetrieval(limit=5),
)
```

Follow the [reference guide](reference/engram_memory.md) for the full lifecycle, error handling, and integration patterns before building.

## Error Handling

Common errors (see the reference's Troubleshooting section for the full list):

- `ENGRAM_API_KEY not set` → set the environment variable; ensure it is an Engram key (`eng_...`), not a Weaviate cluster key.
- `APIError` (422, `user "..." not found`) on search → nothing has ever been added for that `user_id`; catch it and treat as "no memories" (every chatbot's first message from a new user hits this).
- Search returns nothing right after `add` → storage is asynchronous; `await client.runs.wait(run.run_id)` before searching, or check the run status for `failed`.
