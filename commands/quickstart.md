---
description: Interactive onboarding guide — set up Weaviate Cloud, configure credentials, load data, and learn every command
argument-hint:
allowed-tools: Bash, AskUserQuestion, Skill
---

# Weaviate Plugin Quickstart

Welcome the user and walk them through the full setup of the Weaviate plugin, step by step. Be friendly, patient, and thorough — assume the user has never used Weaviate before.

## Step 1: Welcome & Orientation

Greet the user and give a brief overview of what this plugin can do:

- **Search & Query**: Ask questions and get AI-generated answers with citations, or run hybrid/semantic/keyword searches across your data.
- **Collection Management**: Create, list, explore, and inspect collections (like tables in a database, but for vector data).
- **Data Operations**: Import your own data from local CSV/JSON/JSONL files, fetch and filter objects, or load ready-made sample datasets to experiment with.
- **Build Full-Stack Apps**: Use cookbooks to build chatbots, data explorers, RAG pipelines, and AI agents — all powered by Weaviate.

Then ask the user where they are in their journey:

Use AskUserQuestion with these options:
- **"Brand new to Weaviate"** — I don't have an account or cluster yet.
- **"I have a cluster but it's empty"** — I have a Weaviate Cloud account but no data in it yet.
- **"I have a cluster with data"** — I'm ready to start querying.

Route them accordingly:
- Brand new → Continue to Step 2
- Cluster but empty → Skip to Step 3
- Cluster with data → Skip to Step 5

## Step 2: Sign Up for Weaviate Cloud

Guide the user through creating a Weaviate Cloud account:

1. Direct them to **[Weaviate Cloud Console](https://console.weaviate.cloud/signin?utm_source=github&utm_campaign=agent_skills)** to register.
2. Tell them to click either **"Sign in with Google"** or **"Sign in with GitHub"** to sign up.
3. Once registered and logged into the dashboard, guide them to **create a free Sandbox cluster**:
   - Click **"+ Create cluster"**
   - Choose **Sandbox**
   - Enter a cluster name and select a region
   - Click **"Create cluster"** and wait for it to be ready (usually a few minute)
4. Once the cluster is ready, they need two environment variables:
   - **WEAVIATE_URL**: Copy the "REST Endpoint" URL shown under the "Endpoints" section in the cluster dashboard (ends with `.weaviate.cloud`)
   - **WEAVIATE_API_KEY**: Go to **"API Keys"**  section and click "+ New key", once the Create API Key popup appears, add an API key name and select "admin" in the "Role(s)" dropdown. Click on "Create Key" and copy and save the key as you will not be able to see it again.

Tell the user to set these two environment variables in their terminal:

```bash
export WEAVIATE_URL="https://your-cluster-name.weaviate.cloud"
export WEAVIATE_API_KEY="your-api-key-here"
```

Recommend they add these to their shell profile (`~/.zshrc`, `~/.bashrc`, etc.) so they persist across sessions.

Once the user confirms they've done this, verify the environment variables are set:

```bash
[ -z "$WEAVIATE_URL" ] && echo "WEAVIATE_URL is NOT set" || echo "WEAVIATE_URL is set to $WEAVIATE_URL"
[ -z "$WEAVIATE_API_KEY" ] && echo "WEAVIATE_API_KEY is NOT set" || echo "WEAVIATE_API_KEY is set"
```

If either is missing, help them troubleshoot before proceeding.

## Step 3: Verify Prerequisites

Check that the required tools are installed:

```bash
python3 --version
```

```bash
uv --version
```

If `uv` is not installed, offer to install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or suggest alternatives: `pip install uv` or `brew install uv`.

## Step 4: Load Data

Ask the user how they want to get data into their cluster:

Use AskUserQuestion with these options:
- **"Load sample data"** — I want to try example datasets to explore the plugin.
- **"Import my own data"** — I have a CSV, JSON, or JSONL file I want to import.
- **"Create an empty collection"** — I just want to set up a schema and add data later.
- **"Skip for now"** — I'll add data later, just show me the commands.

### If "Load sample data":

Ask which domain interests them using AskUserQuestion:
- **"Academic"** — AI/ML research papers from Arxiv → creates `AI_Arxiv` collection
- **"Finance"** — Synthetic Indian Income Tax Returns → creates `Income_Tax_Returns` collection
- **"E-commerce"** — Product catalog with pricing and categories → creates `Product_Catalog` collection
- **"Medical"** — Hair disease information → creates `Hair_Medical` collection
- **"Customer Support"** — IT helpdesk support tickets → creates `IT_Support_Tickets` collection

Then run the example data script for their chosen domain:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/example_data.py --domain "CHOSEN_DOMAIN"
```

Valid `--domain` values: `academic` (default), `finance`, `ecommerce`, `medical`, `customer_support`.

After it completes, confirm the collection was created:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/list_collections.py
```

### If "Import my own data":

**Important**: The import script only supports **local files** on disk (CSV, JSON, or JSONL). It does not accept remote URLs. If the user's data is at a remote URL, help them download it first before importing:

```bash
curl -L "https://example.com/data.csv" -o /tmp/data.csv
```

Walk the user through importing their local data:

1. Ask them for the **file path** to their data file.
2. Read and explore a small sample of the file to understand its structure (column names, data types, sample values).
3. Ask if they want to:
   - **Create a new collection** — We'll design a schema based on their data.
   - **Import into an existing collection** — We'll inspect the collection schema and verify compatibility.

   **If creating a new collection**:

   Based on the data file you inspected in step 2, design a schema with property names and data types that match the file's columns/keys. Collection names must start with an uppercase letter. Do not specify a vectorizer unless the user explicitly requests one — the default `text2vec_weaviate` is used automatically.

   Supported data types: `text`, `text[]`, `boolean`, `boolean[]`, `int`, `int[]`, `number`, `number[]`, `date`, `date[]`, `uuid`, `uuid[]`, `geoCoordinates`, `phoneNumber`, `blob`, `object`, `object[]`.

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/create_collection.py CollectionName \
     --properties '[{"name": "prop1", "data_type": "text"}, {"name": "prop2", "data_type": "number"}]' \
     --description "Description of the collection"
   ```

   **If importing into an existing collection**:

   First, list available collections so the user can pick one:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/list_collections.py
   ```

   Then inspect the target collection's schema to see its property names and data types:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/get_collection.py --name "COLLECTION_NAME"
   ```

   Compare the collection's property names against the file's column/key names. The import script matches columns to properties **by name (case-sensitive)**. If names don't match, you must provide a `--mapping` to map file columns to collection properties, or the mismatched columns will be silently skipped. Also check if the collection has multi-tenancy enabled — if it does, the `--tenant` flag is **required**.

4. Run the import:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py "PATH_TO_FILE" --collection "COLLECTION_NAME"
   ```

   If column names don't match collection property names, use `--mapping` (maps file column → collection property):

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py "PATH_TO_FILE" --collection "COLLECTION_NAME" \
     --mapping '{"file_column_name": "collection_property_name"}'
   ```

   If the collection has multi-tenancy enabled, add `--tenant`:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/import.py "PATH_TO_FILE" --collection "COLLECTION_NAME" --tenant "tenant_name"
   ```

5. Verify the import by exploring the collection:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/explore_collection.py "COLLECTION_NAME" --limit 3
   ```

   Check that the object count increased and sample objects look correct.

### If "Create an empty collection":

Help the user design their schema interactively. Ask them what kind of data they plan to store and suggest properties and data types. Do not specify a vectorizer unless the user explicitly requests one. Collection names must start with an uppercase letter. Then create it:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/create_collection.py CollectionName \
  --properties '[{"name": "title", "data_type": "text"}, {"name": "content", "data_type": "text"}]' \
  --description "Description of the collection"
```

### If "Skip for now":

Continue to Step 5.

## Step 5: Test Drive — Try Your First Commands

Now that setup is complete, walk the user through a hands-on demo of the key commands. Adapt the examples to use whatever collection they actually have.

### 5a. List Collections

Show them what's in their cluster:

```
/weaviate:collections
```

### 5b. Explore a Collection

Pick one of their collections and explore it:

```
/weaviate:explore "COLLECTION_NAME"
```

Point out the total object count, property metrics, and sample objects.

### 5c. Search

Run a hybrid search using a query relevant to their data:

```
/weaviate:search query "a relevant query" collection "COLLECTION_NAME"
```

Briefly explain the three search types:
- **Hybrid** (default) — Combines keyword matching and semantic similarity. Best for most use cases.
- **Semantic** — Pure vector similarity. Great for finding conceptually related content even with different wording.
- **Keyword** — BM25 keyword matching. Use for exact terms, IDs, or specific text patterns.

### 5d. Ask a Question

Show them the Query Agent, which generates AI-powered answers with source citations:

```
/weaviate:ask query "a relevant question" collections "COLLECTION_NAME"
```

Explain that `/weaviate:ask` gives synthesized answers with citations, while `/weaviate:query` returns raw objects — both can search across multiple collections at once by passing a comma-separated list.

## Step 6: Command & Skill Reference

### Slash Commands

These are shortcut commands you can run anytime:

| Command | What It Does |
|---------|-------------|
| `/weaviate:ask` | Ask a question, get an AI-generated answer with source citations |
| `/weaviate:query` | Search across collections and get raw objects back |
| `/weaviate:search` | Run hybrid, semantic, or keyword search on a collection |
| `/weaviate:collections` | List all collections, or get the detailed schema of one |
| `/weaviate:explore` | See statistics, metrics, and sample data from a collection |
| `/weaviate:fetch` | Fetch specific objects by UUID or with filters |
| `/weaviate:data` | Load a sample dataset (academic, finance, ecommerce, medical, customer_support) |

### Skills (Auto-Discovered)

This plugin also includes two skills with deeper capabilities that go beyond what the slash commands cover. These skills are **automatically discovered** by the agent — you don't need any special syntax to use them. Just describe what you want in natural language.

**Weaviate skill** — The core database skill. The slash commands above are powered by this skill's scripts, but you can also ask the agent directly for more advanced operations like creating collections with custom vectorizers, multi-tenancy, and replication settings, importing data with column mapping and batch size control, or any search/query operation with full parameter control.

**Weaviate Cookbooks skill** — Implementation guides for building full-stack AI applications. These have **no slash commands** — you use them entirely by asking the agent in natural language. Just say what you want to build:

| Cookbook | How To Ask For It |
|---------|------------------|
| **Query Agent Chatbot** | "Build me a chatbot with streaming responses and chat history" |
| **Data Explorer** | "Build a data explorer app with sorting and search" |
| **Basic RAG** | "Set up retrieval-augmented generation for my collection" |
| **Advanced RAG** | "Build a RAG pipeline with query rewriting and re-ranking" |
| **Multimodal RAG (PDF)** | "Build a document search system for my PDFs" |
| **Basic Agent** | "Build a tool-calling AI agent with structured outputs" |
| **Agentic RAG** | "Build a RAG-powered agent with memory" |
| **Frontend Interface** | "Build a Next.js frontend for my Weaviate backend" |

### Pro Tips

- **Don't remember a collection name?** Just run `/weaviate:collections` to see them all.
- **Have data in multiple collections?** `/weaviate:ask` and `/weaviate:query` can search across multiple collections at once — just pass them as a comma-separated list.
- **Data import only works with local files.** If your data is at a remote URL, download it first with `curl` or `wget`, then import the local file.

## Step 7: What's Next?

Ask the user what they'd like to do next using AskUserQuestion:
- **"Search my data"** — Let's run some queries!
- **"Build an app"** — Show me the cookbooks for building full-stack apps.
- **"Import more data"** — I have more data to load.
- **"Just explore"** — I'll take it from here.

Route them to the appropriate command or cookbook based on their choice. If they choose "Build an app", list the available cookbooks and help them pick one — just describe the app they want in natural language and the agent will use the right cookbook automatically.
