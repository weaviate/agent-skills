---
name: cookbooks
description: Collection of best practices and code snippets for building AI applications with Weaviate
disable-model-invocation: true
---

# Weaviate Cookbooks

Use these references when users ask for "one-shot" implementations using Weaviate.

Before generating backend code that initializes a Weaviate client:
1. Read [Environment Requirements](references/environment-requirements.md) for the canonical env var and header mapping.
2. Use provider-specific env var names only (for example, `OPENAI_API_KEY`).
3. Do not introduce generic placeholders like `INFERENCE_API_KEY` or `EXTERNAL_PROVIDER_API_KEY`.

Available references:
- [Environment Requirements](references/environment-requirements.md)
- [Query Agent Chatbot](references/query-agent-chatbot.md)
