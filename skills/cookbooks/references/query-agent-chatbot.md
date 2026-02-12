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
- Use Next.js for frontend and Vercel AI SDK (`useChat`) for chat state/stream integration.
- Depending on user request: consider combining this app with the Data Explorer.
    - If the user explicitly only wants chatbot, create this app independently
    - If the user wants a fully featured chat and data explorer, combine the apps
    - If no explicit instructions are given, ask the user their preference before continuing
    - See the [Combination with Other Cookbooks](#additional-functionalitycombinations-with-other-cookbooks) section for details

## Fast Setup Commands

Project bootstrap:

```bash
uv init chatbot
cd chatbot
uv venv
uv add fastapi 'uvicorn[standard]' weaviate-client weaviate-agents pydantic-settings sse-starlette python-dotenv
```

Frontend bootstrap:

```bash
npx create-next-app@latest frontend --ts --eslint --app --use-npm --import-alias '@/*' --tailwind --yes
cd frontend
npm install ai @ai-sdk/react zod
```

## Workflow Contract (Must Follow)

1. Build backend and frontend in one pass.
2. Create `.env.example` and `.env` template files.
3. Before asking user to fill env, do non-secret local sanity checks that do not require real credentials (imports/compile/startup-shape checks).
4. Ask user to fill real env values.
5. After the user confirms, verify both backend and frontend start without errors and provide exact commands to run them in separate terminals.

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

## Frontend Requirements

- Next.js app in `frontend/`.
- Tailwind is the default styling approach.
- Minimal, sleek, and modern chat UI that can:
  - send non-streaming request to `/chat`
  - receive and render streaming updates from `/chat/stream`
- Keep architecture clean and modular.

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

### Terminal 2 (Frontend)

```bash
cd chatbot/frontend
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Then:
- Ask user to start both terminals.
- Run smoke tests yourself against running services.
- Report pass/fail in plain language and fix blockers.

Do not offload detailed testing steps to the user unless they explicitly ask.

## Troubleshooting

- `OPTIONS /chat/stream 400`: fix CORS origin mismatch (`localhost` vs `127.0.0.1`).
- Weaviate startup host errors: ensure `WEAVIATE_URL` is full `https://...` URL.
- Frontend can open but API calls fail: verify frontend backend base URL and matching host/origin.
- Stream UI not updating: verify SSE parsing and `text/event-stream` behavior.
- For any other issues, refer to the official library/package documentation and use web search extensively for troubleshooting.

## Done Criteria

- Backend healthy.
- `/chat` works.
- `/chat/stream` streams progress/token/final.
- Frontend sends and receives responses.
- User can run both servers in separate terminals with provided commands.

## Additional functionality/combinations with other cookbooks

This app is a chatbot, but you can combine this app with the data explorer: [Data Explorer](./data_explorer.md)

If you combine these apps, make the appropriate steps to combine the functionalities:

- Create or use a directory `/routes` which separate functions for query agent chat and data exploration. Import the routers in the `main.py` file
- Combine the names of `data_explorer` and `chatbot` so they are under the same directory
- The frontend should have multiple pages/tabs depending on design choices so that data exploration and chat is separated
- Consider crossovers between functionalities, e.g. a chat button from the data viewer/collection viewer which takes the user to chat with that collection selected.
- Make any adjustments to the structure of either backends that you deem necessary