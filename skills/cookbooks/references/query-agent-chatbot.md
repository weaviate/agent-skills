## Build Weaviate Query Agent Chatbot (One Shot)

Build a full-stack Query Agent chatbot with minimal back-and-forth. Optimize for developer success.

Read first:

- Weaviate Query Agent usage: https://docs.weaviate.io/agents/query/usage
- Env/header mapping: [Environment Requirements](./environment-requirements.md)

Use `environment-requirements.md` mapping exactly.

## Core Rules

- Use `uv` for Python project/dependency management.
- Do not manually author `pyproject.toml` or `uv.lock`; let `uv` generate/update them.
- Use this backend install set:
  - `uv add fastapi 'uvicorn[standard]' weaviate-client weaviate-agents pydantic-settings sse-starlette python-dotenv`
- If `uv` not available, create a `requirements.txt` for pip installation

## Fast Setup Commands

Project bootstrap:

```bash
uv init chatbot
cd chatbot
uv venv
uv add fastapi 'uvicorn[standard]' weaviate-client weaviate-agents pydantic-settings sse-starlette python-dotenv
```

## Workflow Contract (Must Follow)

1. Build backend in one pass.
2. Create `.env.example` and `.env` template files.
3. Before asking user to fill env, do non-secret local sanity checks that do not require real credentials (imports/compile/startup-shape checks).
4. Ask user to fill real env values.
5. After the user confirms, verify backend starts without errors and provide exact commands to run it in terminal.

Do not ask avoidable questions that you can resolve from context.

## Structure Guidance (Compact)

Use a modular layout like:

```text
chatbot/
  backend/
    app/
      main.py
      config.py
      lifespan.py
      dependencies.py
      routers/
      services/
      models/
    .env.example
    .env
  frontend/
```

Keep these boundaries:

- routers: HTTP only
- services: business/query-agent logic
- models: request/response schemas
- config/lifespan: wiring and startup/shutdown

## Backend Requirements

- FastAPI async app with lifespan.
- Async Weaviate client initialized in lifespan and closed on shutdown.
- Query Agent service layer (`ask` + `ask_stream`).
- Endpoints:
  - `GET /health`
  - `POST /chat`
  - `POST /chat/stream` (SSE)
- Pydantic settings from `.env`.
- Conversation history mapping to Weaviate chat message format.

## Env Rules

Mandatory:

- `WEAVIATE_URL`
- `WEAVIATE_API_KEY`
- `COLLECTIONS`

External provider keys:

- Only fill keys actually used by the target Weaviate collection setup.

CORS:

- Default `CORS_ORIGINS` should include:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`

## Post-Env Hand-Holding (Required)

After user says env is filled, provide:

### Terminal 1 (Backend)

```bash
cd chatbot/backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then:

- Ask user to start the terminal.
- Run smoke tests yourself against running services.
- Report pass/fail in plain language and fix blockers.

Do not offload detailed testing steps to the user unless they explicitly ask.

## Troubleshooting

- `OPTIONS /chat/stream 400`: fix CORS origin mismatch (`localhost` vs `127.0.0.1`).
- Weaviate startup host errors: ensure `WEAVIATE_URL` is full `https://...` URL.

## Done Criteria

- Backend healthy.
- `/chat` works.
- `/chat/stream` streams progress/token/final.
- User can run both server in terminal with provided commands.
