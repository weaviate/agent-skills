---
name: cookbooks
<<<<<<< Updated upstream
description: Use this skill when the user wants to build AI applications with Weaviate. It contains a high-level index of architectural patterns, 'one-shot' blueprints, and best practices for common use cases.
---

# Weaviate Cookbooks

## Overview

This skill provides an index of implementation guides and foundational requirements for building Weaviate-powered AI applications. Use the references to quickly scaffold full-stack applications with best practices for connection management, environment setup, and application architecture.

## Environment Requirements

Before generating backend code that initializes a Weaviate client:
1. Read [Environment Requirements](references/environment-requirements.md) for the canonical env var and header mapping.
2. Use provider-specific env var names only (for example, `OPENAI_API_KEY`).
3. Do not introduce generic placeholders like `INFERENCE_API_KEY` or `EXTERNAL_PROVIDER_API_KEY`.

## Cookbook Index

- [Query Agent Chatbot](references/query-agent-chatbot.md): Build a full-stack Next.js + FastAPI chatbot using Weaviate Query Agent with streaming and chat history support.
=======
description: Collection of best practices and code snippets for building AI applications with Weaviate
---

## Available Cookbooks

### [Multimodal RAG: Building Document Search Systems](multimodal_rag.md)
Learn how to build a multimodal Retrieval-Augmented Generation (RAG) system using ColQwen2 for embeddings and Qwen2.5-VL for generation. This cookbook covers:
- Setting up a complete multimodal RAG pipeline
- Processing documents (PDFs, images) with late-interaction models
- Storing multi-vector embeddings in Weaviate
- Implementing semantic search with MaxSim scoring
- Generating answers using Vision Language Models
>>>>>>> Stashed changes
