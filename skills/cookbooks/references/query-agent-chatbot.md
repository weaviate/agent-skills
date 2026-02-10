## Build Weaviate Query Agent Chatbot Backend

Create a production-ready FastAPI backend for a Weaviate Query Agent chatbot with streaming support. Use `uv` for project management and follow modern Python async patterns.

As a first step, fetch and read the Weaviate Query Agent usage instructions from [here](https://docs.weaviate.io/agents/query/usage).
Before implementing environment configuration, read [Environment Requirements](./environment-requirements.md) in this same folder and use that mapping exactly.

### Project Setup with uv

1. Initialize the project:
   ```bash
   uv init chatbot
   cd chatbot
   uv venv
   ```

2. Add dependencies (uv will create/update pyproject.toml automatically):
   ```bash
   uv add fastapi uvicorn[standard] weaviate-client weaviate-agents pydantic-settings sse-starlette python-dotenv
   ```

3. Create directory structure:
   ```
   chatbot/
   ├── backend/
   │   ├── app/
   │   │   ├── __init__.py
   │   │   ├── main.py              # FastAPI app factory with lifespan
   │   │   ├── config.py            # Pydantic Settings for env vars
   │   │   ├── dependencies.py      # FastAPI dependency injection
   │   │   ├── lifespan.py          # Startup/shutdown handling (Weaviate client)
   │   │   ├── routers/
   │   │   │   ├── __init__.py
   │   │   │   ├── chat.py          # POST /chat (non-streaming), POST /chat/stream
   │   │   │   └── health.py        # Health check endpoint
   │   │   ├── services/
   │   │   │   ├── __init__.py
   │   │   │   └── query_agent.py   # AsyncQueryAgent wrapper/service
   │   │   └── models/
   │   │       ├── __init__.py
   │   │       └── schemas.py       # Pydantic request/response models
   │   ├── .env.example
   │   ├── .gitignore
   │   └── README.md
   └── frontend/
   ```

4. Create root files for backend:
   - `.env.example` with all required variables (no values)
   - `.env` (gitignored) populated from example
   - `.gitignore` (Python standard + .env)
   - `README.md` with setup instructions

### Configuration (backend/app/config.py)

Use Pydantic Settings with `pydantic-settings` to load from .env:

Required settings:
- WEAVIATE_URL: Weaviate Cloud cluster URL
- WEAVIATE_API_KEY: Weaviate Cloud API key
- Provider API keys: Use provider-specific env vars from [Environment Requirements](./environment-requirements.md) (for example `OPENAI_API_KEY`, `COHERE_API_KEY`, `ANTHROPIC_API_KEY`)
- COLLECTIONS: Comma-separated list of collection names to query
- DEFAULT_TIMEOUT: Query Agent timeout (default 60)
- APP_HOST/APP_PORT: Server config (default 0.0.0.0:8000)

### Weaviate Client Lifespan (backend/app/lifespan.py)

Use FastAPI's lifespan context manager to initialize the async Weaviate client and AsyncQueryAgent on startup, properly closing connections on shutdown.

1. Create an async context manager that:
   - Initializes AsyncWeaviateClient using `weaviate.use_async_with_weaviate_cloud()`
   - Creates AsyncQueryAgent with collections from config
   - Stores the agent in `app.state`
   - Yields control
   - Properly closes client on shutdown

### Query Agent Service (backend/app/services/query_agent.py)

Create a service class that wraps `AsyncQueryAgent` with methods for:
- `ask(query, conversation_history)` - non-streaming
- `ask_stream(query, conversation_history)` - returns async generator yielding `ProgressMessage`, `StreamedTokens`, and final response

### Dependencies (backend/app/dependencies.py)

Implement dependency injection for the service:

1. Create a dependency function `get_query_agent_service()` that:
   - Retrieves the pre-initialized agent from `request.app.state`
   - Returns a `QueryAgentService` instance

### Pydantic Models (backend/app/models/schemas.py)

Define these request/response models:

ChatRequest:
- message: str (the current user query)
- conversation_history: Optional[list[ChatMessage]] (for multi-turn)
- collections: Optional[list[str]] (runtime override of default collections)
- stream: bool = False (whether to stream response)

ChatMessage:
- role: Literal["user", "assistant"]
- content: str

StreamResponse:
- type: Literal["progress", "token", "final"]
- data: Union[ProgressData, TokenData, FinalData]

ProgressData: message, details
TokenData: delta (text chunk)
FinalData: final_answer, searches, aggregations, usage, missing_information

### Chat Router (backend/app/routers/chat.py)

Implement two endpoints:

POST /chat
- Accepts ChatRequest
- If conversation_history provided, convert to weaviate ChatMessage objects
- Calls `QueryAgentService.ask()`
- Returns JSON with final_answer and metadata

POST /chat/stream (SSE endpoint)
- Uses EventSourceResponse from sse-starlette
- Calls `QueryAgentService.ask_stream()`
- Iterate over the stream yielding events:
  - ProgressMessage → {"type": "progress", "data": {"message": ..., "details": ...}}
  - StreamedTokens → {"type": "token", "data": {"delta": ...}}
  - Final response → {"type": "final", "data": {...full response object...}}
- Handle exceptions gracefully and yield error events

### Main Application (backend/app/main.py)

- Create FastAPI app with `lifespan` context
- Include `chat` router and `health` router
- Add CORS middleware (allow all origins for development, configurable via env)
- Add health check endpoint GET /health that verifies Weaviate connection
- Use uvicorn.run() in `if __name__ == "__main__"` block

### Environment Files

.env.example:
```
WEAVIATE_URL=https://your-cluster.weaviate.cloud
WEAVIATE_API_KEY=your-weaviate-api-key
OPENAI_API_KEY=your-openai-api-key
COLLECTIONS=Product,Documentation,FAQ
CUSTOM_SYSTEM_PROMPT=
DEFAULT_TIMEOUT=60
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

See [Environment Requirements](./environment-requirements.md) for other provider keys and headers.

.gitignore:
Standard Python gitignore plus:
```
.env
.env.local
.venv/
```

### Key Implementation Details

1. **Streaming Implementation**: Use `AsyncQueryAgent` and map its output to SSE events. Ensure `text/event-stream` media type.

2. **Conversation Handling**: Convert frontend `ChatMessage` models to `weaviate.agents.classes.ChatMessage` before passing to the agent.

3. **Service Layer**: Keep business logic in `services/query_agent.py` to keep routers clean.

4. **Error Handling**: Proper try/except blocks in service and router levels.

5. **Async Pattern**: Use `async`/`await` consistently throughout the stack.

6. **Testing**: Include a simple test script or curl examples in README.

### Frontend Recommendation

We recommend using Next.js (npx create-next-app@latest) with the Vercel AI SDK for the frontend, placed in a `frontend/` directory at the project root. The `useChat` hook handles state management, streaming, and UI updates out of the box. Learn more [here](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat).

### Running the Server

Document that users should:
1. Copy .env.example to .env and fill values
2. Run: `uv run uvicorn app.main:app --reload`
3. Or use: `python -m app.main`

The app should work out of the box once env vars are set. If encountering any issues, use web search to find solutions.
