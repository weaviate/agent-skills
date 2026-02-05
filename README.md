# Weaviate Agent Skills

A [Claude Code plugin](https://code.claude.com/docs/en/plugins) and [Agent Skill](https://agentskills.io) for interacting with [Weaviate](https://weaviate.io) database.


## Compatibility

Works with any agent that supports the [Agent Skills](https://agentskills.io) format.

## Installation

```bash
# Using npx skills (Cursor, Claude Code, Gemini CLI, etc.)
npx skills add weaviate/agent-skills

# Using Claude Code Plugin Manager
claude
/plugin install weaviate/agent-skills

# Manual: clone and point your agent to the directory
git clone https://github.com/weaviate/agent-skills.git

# For Claude Code, after cloning, run 
cd agent-skills
claude --plugin-dir .
```

## Configuration

### Required Environment Variables

```bash
export WEAVIATE_URL="https://your-cluster.weaviate.cloud"
export WEAVIATE_API_KEY="your-api-key"
```

### External Providers API Keys (Auto-Detected)

Set API keys for the providers your collections use. All keys are automatically detected:

| Provider | Environment Variable |
|----------|---------------------|
| OpenAI | `OPENAI_API_KEY` |
| Cohere | `COHERE_API_KEY` |
| HuggingFace | `HUGGINGFACE_API_KEY` |
| Jina AI | `JINAAI_API_KEY` |
| Voyage AI | `VOYAGE_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| NVIDIA | `NVIDIA_API_KEY` |
| Google Vertex AI | `VERTEX_API_KEY` |
| Google AI Studio | `STUDIO_API_KEY` |
| Azure OpenAI | `AZURE_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Anyscale | `ANYSCALE_API_KEY` |
| Databricks | `DATABRICKS_TOKEN` |
| Friendli | `FRIENDLI_TOKEN` |
| xAI | `XAI_API_KEY` |
| AWS | `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` |

## Usage

### Commands (Claude Code Plugin)

```bash
# Ask a question and get an AI-generated answer with citations
/weaviate:ask query "What are the benefits of vector databases?" collections "Documentation"

# Search collections and get raw results
/weaviate:query query "machine learning tutorials" collections "Articles,BlogPosts" limit 5

# Direct search with different search types
/weaviate:search query "product SKU-123" collection "Products" type "keyword"
/weaviate:search query "similar items" collection "Products" type "semantic"
/weaviate:search query "best laptops" collection "Products" type "hybrid" alpha "0.7"
```

### Skills (Any Compatible Agent)

The skill is automatically discovered by compatible agents. Simply describe what you want:

- "Search my Weaviate documentation for information about HNSW indexing"
- "List all my Weaviate collections"
- "Find products similar to 'wireless headphones' in the Products collection"

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A Weaviate Cloud instance

### Python Dependencies

Dependencies are managed per-script using inline metadata. When using `uv run`, dependencies are automatically installed.

## Resources

- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Agent Skills Specification](https://agentskills.io/specification)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Weaviate Query Agent](https://weaviate.io/developers/weaviate/agents)
