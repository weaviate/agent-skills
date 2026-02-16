---
description: Create example data
argument-hint: domain [domain_name] nrows [nrows] vectorizer [vectorizer_name]
allowed-tools: Bash(uv:*), AskUserQuestion, Skill
---

# Create Example Data

Create example data in a specific domain and upload to a Weaviate collection.

## Usage

```
/weaviate:data
/weaviate:data domain "finance" nrows 100
/weaviate:data domain "ecommerce" vectorizer "text2vec-weaviate"
```

## Workflow

1. Run the create example data script:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/example_data.py
   ```
2. Confirm the collection exists
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/weaviate/scripts/get_collection.py --name "COLLECTION_NAME"
   ```
   
**Domain Datasets:**

- `academic` contains a selection of chunked papers from Arxiv on the topic of AI/ML. Creates the `AI_Arxiv` collection 
- `finance` creates a fully synthetic dataset of Indian Income Tax Return forms. Creates the `Income_Tax_Returns` collection
- `ecommerce` contains structured e-commerce product information including product details, pricing, categorization. Creates the `Product_Catalog` collection
- `medical` contains information about common hair related diseases. Creates the `Hair_Medical` collection
- `customer_support` contains customer support tickets from IT. Creates the `IT_Support_Tickets` collection

No other domains are supported.

## Environment

Requires:
- `WEAVIATE_URL`: Weaviate Cloud cluster URL
- `WEAVIATE_API_KEY`: API key for authentication