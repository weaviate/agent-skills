## Build Data Explorer App (One Shot)

Build a full-stack Data Explorer App for Weaviate Collections with FastAPI. 

Read first:
- Search patterns and basics in Weaviate: https://docs.weaviate.io/weaviate/search/basics
- Filters in Weaviate: https://docs.weaviate.io/weaviate/search/filters
- Env/header mapping: [Environment Requirements](./environment-requirements.md)

Use `environment-requirements.md` mapping exactly.

## Core Rules

- Use a virtual environment via `venv`
- Use `uv` for Python project/dependency management.
- Do not manually author `pyproject.toml` or `uv.lock`; let `uv` generate/update them.
- Use this backend install set:
  - `uv add fastapi 'uvicorn[standard]' weaviate-client weaviate-agents pydantic-settings sse-starlette python-dotenv`
- Use Next.js for frontend 
- Depending on user request: consider combining this app with the Query Agent Chatbot.
    - If the user explicitly only wants a data viewer/explorer, create this app independently
    - If the user wants a fully featured chat and data explorer, combine the apps
    - If no explicit instructions are given, ask the user their preference before continuing
    - See the [Combination with Other Cookbooks](#additional-functionalitycombinations-with-other-cookbooks) section for details

## Fast Setup Commands

Project bootstrap:

```bash
uv init data_explorer
cd data_explorer
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
- Ensure no async blocking operations.
- Not a full CRUD implementation - this is only for viewing data in a Weaviate collection.
- Endpoints for:
  - `GET /health`
  - `GET /env_check`: returns what API keys are missing (if any) for verification on app start
  - `GET /collections`: return available collections
  - `GET /data/{collection_name}?xx=xx&yy=yy`: return data with optional arguments (more later), and pagination
- Pydantic settings from `.env`.
- Conversation history mapping to Weaviate chat message format.

## Frontend Requirements

- Next.js app in `frontend/`.
- Tailwind is the default styling approach.
- Minimal, sleek, and modern UI that can:
  - views Weaviate collection data in a tabular format
  - can click on table headings to enable sorting on that property (if available)
  - can click on individual cells to view datum in full
- Main functionality:
  - send GET request to `/env_check` to see if the user needs to configure any environment variables
  - send GET request to `/collections` to retrieve available collections before accessing tables. Tables can be viewed once a collection is clicked on
  - send GET request per-collection to view data
- Keep architecture clean and modular.

## Env Rules

Mandatory:
- `WEAVIATE_URL`
- `WEAVIATE_API_KEY`

External provider keys:
- Only fill keys actually used by the target Weaviate collection setup.

CORS:
- Default `CORS_ORIGINS` should include:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`

## FastAPI standards

1. Do not use hardcoded status values, use `status` from FastAPI, for example:

```python
from fastapi import status
status.HTTP_200_OK # code 200
status.HTTP_404_NOT_FOUND # code 404
# and more
```

2. Use a Pydantic `BaseModel` for the `request` and `response_model` in all endpoints that require it. Ensure schema validation to mitigate user-error on the API.

3. Use path parameters and query parameters for GET endpoints instead of payloads, for example:

```python
@app.get("/items/{item_id}")
async def read_item(item_id: str):
    return {"item_id": item_id}
```
```python
@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

4. Implement best practices for error-handling, do early returns and provide the correct status codes when necessary.

5. Use proper logging for API usage, not simple print statements.

## FastAPI endpoints

Basic structure of endpoints. Customise according to user preference or suitability. Do not follow exactly, this is a guideline only.

Ensure you also set up standard FastAPI procedures, such as global error handling, logging, dependencies. Set up an async client manager that connects on startup (via lifespan) and closes gracefully on app exit, use a dependency injection to add the client to the relevant endpoints.

### GET /health

This is a standard health check. For example:

```python
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str

@app.get("/health", tags=["health"], response_model=HealthResponse)
async def health_check() -> HealthResponse:
    logger.info("Health check requested")
    return HealthResponse(status="healthy")
```

### GET /env_check

Check what environment variables the backend has access to, used to verify the user's Weaviate configuration is correct (preventing errors on the frontend). For example:

```python
import os
from pydantic import BaseModel

class EnvCheckResponse(BaseModel):
    weaviate_url: bool
    weaviate_api_key: bool

@app.get("/env_check", tags=["health"])
async def env_check() -> EnvCheckResponse:
    logger.info("Environment check requested")
    return EnvCheckResponse(
        weaviate_url = os.getenv("WEAVIATE_URL") is not None,
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY") is not None,
    )
```

### GET /collections

Check what collections are available. For example:

```python
from pydantic import BaseModel
from weaviate.client import WeaviateAsyncClient

class CollectionsResponse(BaseModel):
    collections: list[str]

@app.get("/collections", tags=["collections"])
async def collections() -> CollectionsResponse:

    # include client management to import async client here

    logger.info("Collections requested")
    collections = await client.collections.list_all()
    return CollectionsResponse(
        collections = list(collections.keys())
    )
```

Tip: consider expanding this endpoint to include collection descriptions and configs. `await client.collections.list_all()` returns `dict[str, _CollectionConfigSimple]` where `_CollectionConfigSimple` contains attributes:
- `description`: `str`
- `properties`: `list[Property]` where `Property` has `.name`, `.description` and `.data_type` (accessed via `.data_type[:]` to get name of data type as string)
- `vector_config`: `dict[str, _NamedVectorConfig]` where `_NamedVectorConfig` has attribute `.vectorizer.vectorizer` (not a typo) which can be accessed via `.vectorizer.vectorizer[:]` to get the name of the vectoriser as a string.

Multi-tenancy should be checked via 

```python
config = await collection.config.get()
config.multi_tenancy_config.enabled # bool
```

This is not available in the `_CollectionConfigSimple`, it must be fetched from `collection.config.get()`.

### GET /data/{collection_name}

Retrieve data from a collection, using pagination, sorting and filters.

```python
from weaviate.collections import CollectionAsync
from fastapi import Query
from pydantic import BaseModel
from typing import Any

async def get_collection_data_types(collection: CollectionAsync) -> dict[str, str]:
    config = await collection.config.get()
    properties = config.properties
    return {prop.name: prop.data_type[:] for prop in properties}

class GetDataResponse(BaseModel):
    data_types: dict[str, str]
    items: list[dict[str, Any]]

@router.post("/data/{collection_name}")
async def get_data(
    collection_name: str,
    page_size: int = Query(default=10, ge=1, le=100),
    page_number: int = Query(default=1, ge=1),
    query: str = Query(default=""),
    sort_on: str = Query(default=None),
    ascending: bool = Query(default=True),
) -> GetDataResponse:
    
    # include client management to import async client here

    collection = await client.collections.use(collection_name)
    data_types = await async_get_collection_data_types(collection)

    if query != "":
        response = await collection.query.bm25(
            query=query,
            limit=page_size,
            offset=page_size * (page_number - 1),
        )
    elif sort_on is not None:
        response = await collection.query.fetch_objects(
            sort=Sort.by_property(name=sort_on, ascending=ascending),
            limit=page_size,
            offset=page_size * (page_number - 1),
        )
    else:
        response = await collection.query.fetch_objects(
            limit=page_size,
            offset=page_size * (page_number - 1),
        )

    return GetDataResponse(data_types = data_types, items = [obj.properties for obj in response.objects])
```

Tip: some collections can have multi-tenancy.
Consider adding the tenant as an optional query parameter to `get_data`, e.g.

```python
async def get_data(
    ... # existing args
    tenant: str | None = Query(default=None)
):
    base_collection = await client.collections.use(collection_name)
    data_types = await async_get_collection_data_types(collection)

    config = await collection.config.get()
    if config.multi_tenancy_config.enabled and tenant and tenant.strip():
        collection = base_collection.with_tenant(tenant)
    else:
        collection = base_collection

    # ...existing code
```
Update the frontend to be able to tab through multi-tenant collections. 


## Post-Env Hand-Holding (Required)

After user says env is filled and app is created, provide:

### Terminal 1 (Backend)

```bash
cd data_explorer/backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 (Frontend)

```bash
cd data_explorer/frontend
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Then:
- Ask user to start both terminals.
- Run smoke tests yourself against running services.
- Report pass/fail in plain language and fix blockers.

Do not offload detailed testing steps to the user unless they explicitly ask.

## Troubleshooting

- Weaviate startup host errors: ensure `WEAVIATE_URL` is full `https://...` URL.
- Frontend can open but API calls fail: verify frontend backend base URL and matching host/origin.
- For any other issues, refer to the official library/package documentation and use web search extensively for troubleshooting.

## Done Criteria

- Backend healthy.
- All endpoints work.
- Frontend sends and receives responses.
- User can run both servers in separate terminals with provided commands.

## Additional functionality/combinations with other cookbooks

This app is a data explorer, but you can combine this app with the query agent chatbot: [Query Agent Chatbot](./query-agent-chatbot.md)

If you combine these apps, make the appropriate steps to combine the functionalities:

- Create or use a directory `/routes` which separate functions for query agent chat and data exploration. Import the routers in the `main.py` file
- Combine the names of `data_explorer` and `chatbot` so they are under the same directory
- The frontend should have multiple pages/tabs depending on design choices so that data exploration and chat is separated
- Consider crossovers between functionalities, e.g. a chat button from the data viewer/collection viewer which takes the user to chat with that collection selected.
- Make any adjustments to the structure of either backends that you deem necessary