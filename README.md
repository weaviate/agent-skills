![Weaviate Agent Skills](banner.jpg)

# Weaviate Agent Skills

Agent Skills to help developers build and use AI agents with Weaviate more effectively. Each skill is a  folder containing instructions, scripts, and resources that agents like Claude Code, Cursor, GitHub Copilot, and others can discover to work more accurately and efficiently

Works with any agent that supports the [Agent Skills](https://agentskills.io/home#adoption) format.

## Installation

```bash
# Using npx skills (Cursor, Claude Code, Gemini CLI, etc.)
npx skills add weaviate/agent-skills

# Using Claude Code Plugin Manager
/plugin marketplace add weaviate/agent-skills
/plugin install weaviate@weaviate-plugins

# Manual: clone and point your agent to the directory
git clone https://github.com/weaviate/agent-skills.git
cd agent-skills
claude --plugin-dir .
```

## Configuration

### Weaviate Cloud

It is recommended to create a free cluster in the [weaviate console](https://console.weaviate.cloud/signin?utm_source=github&utm_campaign=agent_skills).

### Required Environment Variables

```bash
export WEAVIATE_URL="https://your-cluster.weaviate.cloud"
export WEAVIATE_API_KEY="your-api-key"
```

### External Provider Keys (Auto-Detected)

For the complete env var list and header mapping, see:

- [Environment Requirements](./skills/cookbooks/references/environment-requirements.md)

## Available Skills

<details>
<summary><strong>Weaviate</strong></summary>

Utility functions for the agent to directly interact with a Weaviate database.

- Create Collections

- Explore Collections (Aggregation, Metadata, Schema)

- Query Collections (Keyword-, Vector-, Hybrid Search) (Support filters)

- Import Data (supports multi-vector and PDF ingestion)

- Query Agent
</details>

<details>
<summary><strong>Cookbooks</strong></summary>

Blueprints for complete end-to-end AI applications with state-of-the art guidelines for agentic infrastructure.

- Multimodal PDF Ingestion

- Data Explorer

- Retrieval Augmented Generation (Basic, Advanced, Agentic)

- Agents

- Query Agent Chatbot

- Frontend Interface (optional)

</details>

## Usage

### Commands (Claude Code Plugin)

```bash
# Ask a question and get an AI-generated answer with source citations
/weaviate:ask query "What are the benefits of vector databases?" collections "Documentation"

# Search collections and get raw results
/weaviate:query query "machine learning tutorials" collections "Articles,BlogPosts" limit 5

# Search with different search types
/weaviate:search query "product SKU-123" collection "Products" type "keyword"
/weaviate:search query "similar items" collection "Products" type "semantic"
/weaviate:search query "best laptops" collection "Products" type "hybrid" alpha "0.7"

# List collections or get a collection's schema
/weaviate:collections
/weaviate:collections name "Articles"

# Explore data in a collection
/weaviate:explore "Products" limit 10

# Fetch objects by ID or with filters
/weaviate:fetch collection "Articles" id "UUID"
/weaviate:fetch collection "Articles" filters '{"property": "category", "operator": "equal", "value": "Science"}'
```

### Skills (Any Compatible Agent)

The skill is automatically discovered by compatible agents. Simply describe what you want:

- "Search my Weaviate documentation for information about HNSW indexing"
- "List all my Weaviate collections"
- "Find products similar to 'wireless headphones' in the Products collection"
- "Build a chatbot using the Query Agent"
- "Build a multimodal RAG app for my PDF documents"
- "Build an agentic RAG app"

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [Weaviate Cloud](https://console.weaviate.cloud/) instance

## Resources

- eBooks
    - [The Context Engineering Guide](https://weaviate.io/ebooks/the-context-engineering-guide?utm_source=github&utm_campaign=agent_skills)
    - [Agentic Architecture Ebook](https://weaviate.io/ebooks/agentic-architectures?utm_source=github&utm_campaign=agent_skills)
    - [Advanced RAG Techniques](https://weaviate.io/ebooks/advanced-rag-techniques?utm_source=github&utm_campaign=agent_skills)
- [Weaviate Query Agent](https://docs.weaviate.io/agents/query)
- [Weaviate Documentation](https://docs.weaviate.io/weaviate)
- [Agent Skills Specification](https://agentskills.io/specification)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
