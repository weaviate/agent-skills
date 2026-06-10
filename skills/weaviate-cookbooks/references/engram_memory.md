# Memory Management with Engram

Add persistent, long-term memory to AI applications using Engram, Weaviate's managed memory server for LLM agents. Engram automatically extracts, consolidates, and stores memories from raw text or conversations, and retrieves them with vector, keyword, or hybrid search.

Use this cookbook when the user wants their app to remember things across sessions: user preferences, profiles, past interactions, or lessons learned by an agent (continual learning).

Read if integrating with an agent or chatbot:
- [Basic Agent Cookbook](./basic_agent.md) — for the `RouterAgent` and tool design patterns used below.
- [Query Agent Chatbot](./query_agent_chatbot.md) — for the chatbot integration pattern.

Docs to reference if needed:
- Engram docs (overview): https://docs.weaviate.io/engram
- Quickstart: https://docs.weaviate.io/engram/quickstart
- Concepts (memories, topics, scopes, groups, pipelines): https://docs.weaviate.io/engram/concepts
- Guides (store, search, manage, run status): https://docs.weaviate.io/engram/guides
- Engram deep dive blog: https://weaviate.io/blog/engram-deep-dive

## Core Rules

- Use a virtual environment via `venv`
- Use `uv` for Python project/dependency management.
- Do not manually author `pyproject.toml` or `uv.lock`; let `uv` generate/update them.
- Use this install set: `uv add weaviate-engram python-dotenv` (see [Installation](#installation) — Engram is a separate package, not part of `weaviate-client`)
- If combining with an agent (recommended pairing), also follow the install set from [Basic Agent](./basic_agent.md): `uv add dspy`
- Customise this cookbook to the users specification, ask them for details if not given.
- Engram is a managed service accessed via Weaviate Cloud. If the user does not have an Engram project, direct them to [Weaviate Cloud](https://console.weaviate.cloud/signin?utm_source=github&utm_campaign=agent_skills) to create one and generate an Engram API key.
- Do not build a hand-rolled memory system (e.g. a raw Weaviate collection with manual inserts) when the user asks for memory — Engram handles extraction, deduplication, and consolidation out of the box. The manual approach in [Agentic RAG](./agentic_rag.md) is only for users who explicitly want full control or self-hosting.

## Env Rules

Mandatory:
- `ENGRAM_API_KEY` — Engram API key from Weaviate Cloud (format `eng_...`). This carries the project identity; `WEAVIATE_URL`/`WEAVIATE_API_KEY` are not needed for Engram itself.

Optional (only when combining with an agent/chatbot):
- An LLM provider API key (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`)

## Engram Overview

Key concepts (use these terms with the user):

| Concept | Meaning |
|---------|---------|
| **Memory** | A discrete piece of stored information, automatically embedded for semantic search. Fields: `id`, `content`, `topic`, `group`, `user_id`, `properties`, `created_at`, `updated_at`, `score` (search only). |
| **Topic** | A category of memory with a natural-language description that guides LLM extraction (e.g. `food_preferences`: "What food the user likes to eat"). Only information matching a topic is stored. |
| **Group** | A named bundle of topics + pipeline, mapping 1:1 to a use case. Every project has a `default` group; all calls use it unless `group=` is passed. |
| **Scope** | Isolation boundary: project-wide (shared, from the API key), user-scoped (`user_id`, strict isolation), or custom `properties` (e.g. `conversation_id`). |
| **Pipeline / Run** | Storage is asynchronous. `add` returns a `run_id` immediately; the pipeline extracts facts, transforms them against existing memories (dedupe, merge, rewrite), and commits. |

Topics and groups are configured per project in the Weaviate Cloud console (starter templates exist for personalization and continual learning). Code interacts with them by name — do not assume you can create topics from the SDK; ask the user what topics their project defines, or assume the template default (e.g. `UserKnowledge`).

## Installation

Engram ships as its own Python SDK, `weaviate-engram`. It does **not** come with `weaviate-client` (or `weaviate-agents`) — installing those does not give you Engram, and Engram does not require them.

```bash
uv add weaviate-engram

# or with pip
pip install weaviate-engram
```

Note the package name and import name differ: install `weaviate-engram`, import `engram`:

```python
from engram import AsyncEngramClient
```

## Client Setup

Use the async client (`AsyncEngramClient`) — memory calls sit in request paths and event loops (FastAPI, chat backends, agents), so they should not block. A synchronous `EngramClient` with the identical surface (drop the `await`) exists for scripts and sync-only frameworks.

```python
import os
from dotenv import load_dotenv
from engram import AsyncEngramClient

load_dotenv()
client = AsyncEngramClient(api_key=os.environ["ENGRAM_API_KEY"])
```

All `client.memories.*` and `client.runs.*` methods below are coroutines — call them with `await` from async code. See [Async Client](./async_client.md) for general async patterns (lifecycle, FastAPI integration) that apply here too.

## Storing Memories

`client.memories.add(...)` is fire-and-forget: it returns a run immediately and processes in the background. All three input types share optional parameters `user_id`, `properties`, and `group` (defaults to `"default"`).

**String input** — raw text, Engram extracts the facts:

```python
run = await client.memories.add(
    "The user prefers dark mode and works primarily in Python.",
    user_id="alice",
)
print(run.run_id, run.status)  # status: "running"
```

**Conversation input** — chat transcripts (OpenAI Chat Completions message format; roles `user`, `assistant`, `system`, `tool`, `developer` are supported):

```python
run = await client.memories.add(
    [
        {"role": "user", "content": "I just moved to Berlin."},
        {"role": "assistant", "content": "Welcome to Berlin!"},
        {"role": "user", "content": "I prefer specialty coffee."},
    ],
    user_id="alice",
)
```

**Pre-extracted input** — you did the extraction yourself; items skip LLM extraction and go straight to transform + commit. Each item targets a topic by name:

```python
from engram import PreExtractedInput, PreExtractedItem

run = await client.memories.add(
    PreExtractedInput(items=[
        PreExtractedItem(content="User prefers dark mode", topic="UserKnowledge"),
        PreExtractedItem(content="User works in Python", topic="UserKnowledge"),
    ]),
    user_id="alice",
)
```

### Run Status

Storage is async, so a search immediately after `add` may not see new memories. Block until processing finishes when tests or demos need read-after-write:

```python
status = await client.runs.wait(run.run_id)
print(status.status)                # "completed"
print(status.committed_operations)  # which memories were created/updated/deleted
```

Run statuses: `running`, `in_buffer` (paused at a buffer step waiting for a count/time trigger), `completed`, `failed`. In production chat loops, do not wait — fire and forget.

## Searching Memories

```python
results = await client.memories.search(
    query="What programming language does the user prefer?",
    user_id="alice",
)
for memory in results:
    print(memory.content, memory.topic, memory.score)
```

**Retrieval types** — pass `retrieval_config`; hybrid is the default general-purpose choice:

```python
from engram import VectorRetrieval, BM25Retrieval, HybridRetrieval

results = await client.memories.search(
    query="user preferences",
    user_id="alice",
    retrieval_config=HybridRetrieval(limit=10),  # or VectorRetrieval / BM25Retrieval
)
```

**Filter by topic:**

```python
results = await client.memories.search(
    query="user preferences",
    topics=["UserKnowledge"],
    user_id="alice",
    retrieval_config=HybridRetrieval(limit=10),
)
```

**Custom scope properties** — narrow by e.g. conversation. At search time properties are optional filters (omitting one searches across all values); at add time every property the target topic is scoped by must be provided:

```python
from engram import Topic

results = await client.memories.search(
    query="what did we decide?",
    user_id="alice",
    properties={"conversation_id": "abc-123"},
    topics=[
        "user_facts",
        Topic(name="messages", properties={"conversation_id": None}),  # per-topic override
    ],
)
```

## Managing Memories

Get or delete an individual memory by ID (IDs come from search results or `committed_operations`):

```python
memory = await client.memories.get(memory_id, user_id="alice", group="default")

await client.memories.delete(memory_id, user_id="alice", group="default")
```

## Integration Pattern: Chatbot Memory

The standard pattern for chatbots: search memories before generating, add the exchange after responding.

```python
async def chat_turn(user_id: str, user_message: str, generate) -> str:
    # 1. Recall relevant memories for this message
    memories = await client.memories.search(
        query=user_message,
        user_id=user_id,
        retrieval_config=HybridRetrieval(limit=5),
    )
    memory_context = "\n".join(f"- {m.content}" for m in memories)

    # 2. Generate with memories in context (any LLM framework)
    response = generate(user_message, memory_context)

    # 3. Store the exchange — the add call returns as soon as the run is
    #    accepted; processing happens server-side. Do not wait on the run.
    await client.memories.add(
        [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response},
        ],
        user_id=user_id,
    )
    return response
```

`generate` is the user's generation function — e.g. the `generate` from [Basic RAG](./basic_rag.md) with `memory_context` prepended to the context.

## Integration Pattern: Agent Memory Tools

Expose Engram as tools on the `RouterAgent` from [Basic Agent](./basic_agent.md), so the agent decides when to recall or remember:

```python
async def search_memories(query: str) -> str:
    """Search the user's long-term memory for facts, preferences, and past interactions.
    Use when answering may depend on something the user said in a previous session."""
    results = await client.memories.search(
        query=query,
        user_id=CURRENT_USER_ID,
        retrieval_config=HybridRetrieval(limit=5),
    )
    return "\n".join(m.content for m in results) or "No relevant memories found."


async def store_memory(fact: str) -> str:
    """Save an important fact about the user to long-term memory.
    Use when the user states a lasting preference, correction, or piece of personal context."""
    run = await client.memories.add(fact, user_id=CURRENT_USER_ID)
    return f"Memory stored (run {run.run_id})."


router = RouterAgent(model="<model_name>", tools=[search_memories, store_memory])
```

`CURRENT_USER_ID` should come from the app's session/auth context — set it per request, never hardcode it in multi-user apps.

The `RouterAgent` from [Basic Agent](./basic_agent.md) calls tools synchronously (`tool_result = tool_function(**tool_inputs)`). With async tools, make `get_response` an `async def` and await coroutine tools:

```python
import inspect

tool_result = tool_function(**tool_inputs)
if inspect.isawaitable(tool_result):
    tool_result = await tool_result
```

If the agent framework is strictly synchronous and cannot be adapted, use the sync `EngramClient` inside the tools instead.

For **continual learning** (project-wide agent memory, e.g. "filter on the genres property instead of doing a near-text query"), use a project-wide topic and omit `user_id` — lessons learned from one user's sessions then benefit all users. This is configured in the project's topics (the continual learning template).

## REST API (non-Python stacks)

Same operations over HTTP, with `Authorization: Bearer $ENGRAM_API_KEY`:

```bash
# Store
curl -X POST https://api.engram.weaviate.io/v1/memories \
  -H "Authorization: Bearer $ENGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"string": {"content": ["The user prefers dark mode."]}}, "user_id": "alice"}'

# Search
curl -X POST https://api.engram.weaviate.io/v1/memories/search \
  -H "Authorization: Bearer $ENGRAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "What editor does the user prefer?", "user_id": "alice", "retrieval_config": {"retrieval_type": "hybrid", "limit": 5}}'

# Run status
curl https://api.engram.weaviate.io/v1/runs/{run-id} \
  -H "Authorization: Bearer $ENGRAM_API_KEY"
```

Use this for TypeScript/Next.js backends (see [Frontend Interface](./frontend_interface.md)) — call the REST API from server-side routes only, never expose `ENGRAM_API_KEY` to the browser.

## User-specific Customisations

If not specified ask the user about these points before implementing:

**Memory use case**

- Personalization (per-user preferences/profile) → user-scoped topics, always pass `user_id`.
- Continual learning (agent improves from experience, shared across users) → project-wide topics, no `user_id`.
- Both → separate topics (or separate groups) in the same project; scoping is per topic.

**Topics**

What should the app remember? Each distinct category should be a topic with a clear natural-language description — descriptions directly control what the extraction LLM stores. For a single running summary or profile per user, use a bounded topic (max one memory per scope, updated in place) rather than accumulating facts.

**Input type**

- Chat app → conversation input per exchange.
- Event/log style data ("User viewed page X") → string input.
- The user already extracts facts with their own LLM logic → pre-extracted input.

**Retrieval**

Hybrid is the right default. Vector for purely conceptual recall, BM25 for exact terms/IDs. Ask what `limit` fits their context budget (5–10 is typical).

## Troubleshooting

- Searches return nothing right after `add`: processing is asynchronous — `await client.runs.wait(run.run_id)` before searching, or check the run status for `failed`.
- Run stuck at `in_buffer`: the group's pipeline has a buffer step waiting for a count/time trigger; this is expected behaviour, not an error.
- Facts not being stored: only information matching a configured topic description is extracted — check the project's topics in the Weaviate Cloud console and tighten/broaden their descriptions.
- Scope errors on `add`: every scope property required by the target topic (including `user_id` for user-scoped topics) must be provided.
- 401/403 errors: ensure `ENGRAM_API_KEY` is set and is an Engram key (`eng_...`), not a Weaviate cluster API key.
- For any other issues, refer to the official docs at https://docs.weaviate.io/engram and use web search extensively for troubleshooting.

## Done Criteria

- Create test scripts to check store → wait → search → get → delete work end-to-end against the user's Engram project (use a throwaway `user_id` and clean up created memories). Tear down tests after completion, or create a proper test suite with pytest (requires install).
- Memory writes in the app are fire-and-forget; nothing in the request path blocks on `runs.wait`.
- User has completed specification of the app.
