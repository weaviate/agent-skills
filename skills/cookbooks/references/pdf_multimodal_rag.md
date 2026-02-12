# Multi-vector RAG: Building Multimodal Document Search Systems With Weaviate

## Overview

This cookbook provides instructions for implementing a Multimodal Retrieval-Augmented Generation (RAG) system over PDF document collections using ColQwen2 for embeddings and Qwen2.5-VL for generation.

## Architecture

A multimodal RAG system consists of two main pipelines:

### 1. Ingestion Pipeline

- Documents (PDFs, images) are processed by a multimodal late-interaction model
- Multi-vector embeddings are generated and stored in a vector database
- Each document page/section is represented as a collection of vectors

### 2. Query Pipeline

- Text queries are embedded using the same multimodal model
- Relevant documents are retrieved using similarity search (e.g., MaxSim)
- Retrieved documents are passed to a Vision Language Model (VLM) with the query
- The VLM generates a natural language response based on visual and textual context

## Prerequisites

Read first:

- Env/header mapping: [Environment Requirements](./environment-requirements.md)

Use `environment-requirements.md` mapping exactly.

### Hardware Requirements

- GPU with 5-10 GB memory (recommended) or Apple Silicon
- Can run on CPU but will be significantly slower
- Consider cloud options (Google Colab, AWS, etc.) if local resources are limited

### Software Requirements

- Python 3.11 or higher
- PyTorch with appropriate device support (CUDA, MPS, or CPU)
- `uv` package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))

**Install uv if needed:**

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with Homebrew
brew install uv
```

## Step 1: Setup Project and Install Dependencies

### Project Bootstrap

Initialize a new project with `uv`:

```bash
uv init multimodal-rag
cd multimodal-rag
uv venv
```

### Install Core Dependencies

Install required libraries using `uv`:

```bash
uv add colpali_engine weaviate-client qwen_vl_utils
uv add "colpali-engine[interpretability]>=0.3.2,<0.4.0"
```

**Package breakdown:**

- `colpali_engine`: Provides ColQwen2 model and processor
- `weaviate-client`: Python client for Weaviate vector database (v4.x)
- `qwen_vl_utils`: Utilities for processing Qwen2.5-VL inputs
- `colpali-engine[interpretability]`: Optional visualization tools for similarity maps

### Additional Dependencies (Install as Needed)

```bash
# For loading Hugging Face datasets
uv add datasets

# For PDF processing (pdf2image requires poppler to be installed!)
uv add pdf2image pillow
```

## Step 2: Prepare Your Document Dataset

### Option A: Load Existing Dataset

If using a pre-existing dataset:

- Use Hugging Face `datasets` library
- Ensure dataset contains document images or can be converted to images
- Verify image format compatibility with your embedding model

### Option B: Process Your Own Documents

For custom document collections:

1. Convert documents to images (if not already images)
   - PDFs: Use `pdf2image` or similar libraries
   - Office documents: Convert to PDF first, then to images
2. Organize with metadata (document ID, page number, title, etc.)
3. Store in a format suitable for batch processing

**Recommended structure:**

```python
{
    "document_id": str,
    "page_number": int,
    "image": PIL.Image,
    "metadata": dict  # title, author, date, etc.
}
```

## Step 3: Load ColQwen2 Model

### About ColQwen2

ColQwen2 is a multimodal late-interaction model for document retrieval:

- **License**: Apache 2.0 (permissive for commercial use)
- **Base Model**: Built on Qwen2 vision-language model
- **Model Size**: ~5 GB download, similar memory usage
- **Architecture**: Contextualized Late Interaction over Qwen2
- **Model ID**: `vidore/colqwen2-v1.0`

### Loading the Model

```python
import os
import torch
from transformers.utils.import_utils import is_flash_attn_2_available
from colpali_engine.models import ColQwen2, ColQwen2Processor

# Prevent tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Detect available device
if torch.cuda.is_available():
    device = "cuda:0"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

# Choose attention implementation
if is_flash_attn_2_available():
    attn_implementation = "flash_attention_2"
else:
    attn_implementation = "eager"

print(f"Using device: {device}")
print(f"Using attention implementation: {attn_implementation}")

# Load ColQwen2 model (~5 GB download)
model_name = "vidore/colqwen2-v1.0"

model = ColQwen2.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map=device,
    attn_implementation=attn_implementation,
).eval()

# Load ColQwen2 processor
processor = ColQwen2Processor.from_pretrained(model_name)
```

### Create ColQwen2 Embedding Wrapper

Implement a wrapper class for ColQwen2 embedding operations:

```python
class ColQwen2Embedder:
    def __init__(self, model, processor):
        """Initialize with a loaded ColQwen2 model and processor."""
        self.model = model
        self.processor = processor

    def embed_image(self, image):
        """Generate multi-vector embedding for a PIL image.

        Args:
            image: PIL.Image object

        Returns:
            torch.Tensor of shape (num_patches, embedding_dim)
        """
        image_batch = self.processor.process_images([image]).to(self.model.device)
        with torch.no_grad():
            image_embedding = self.model(**image_batch)
        return image_embedding[0]

    def embed_text(self, query):
        """Generate multi-vector embedding for text query.

        Args:
            query: String text query

        Returns:
            torch.Tensor of shape (num_tokens, embedding_dim)
        """
        query_batch = self.processor.process_queries([query]).to(self.model.device)
        with torch.no_grad():
            query_embedding = self.model(**query_batch)
        return query_embedding[0]

# Instantiate the embedder
embedder = ColQwen2Embedder(model, processor)
```

**Notes:**

- Images are embedded as multi-vectors with shape `(num_patches, 128)` where num_patches depends on image size
- Queries are embedded as multi-vectors with shape `(num_tokens, 128)` where num_tokens is the query length
- Reducing image resolution speeds up embedding and produces fewer vectors

## Step 4: Configure Vector Database

### Weaviate Connection

**Weaviate Cloud**

```python
import os
import weaviate
from weaviate.classes.init import Auth

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY),
)
```

### Create Collection Schema

Define a collection with multi-vector support for ColQwen2 embeddings:

```python
import weaviate.classes.config as wc
from weaviate.classes.config import Configure

collection_name = "PDFDocuments"  # Use a descriptive name for your use case

collection = client.collections.create(
    name=collection_name,
    properties=[
        wc.Property(name="page_id", data_type=wc.DataType.INT),
        wc.Property(name="document_id", data_type=wc.DataType.TEXT),
        wc.Property(name="page_number", data_type=wc.DataType.INT),
        wc.Property(name="title", data_type=wc.DataType.TEXT),
        # Add other metadata properties as needed
    ],
    vector_config=[
        Configure.MultiVectors.self_provided(
            name="colqwen",
            # Optional: Use MUVERA encoding for compression
            # encoding=Configure.VectorIndex.MultiVector.Encoding.muvera(),
            vector_index_config=Configure.VectorIndex.hnsw(
                multi_vector=Configure.VectorIndex.MultiVector.multi_vector()
            )
        )
    ]
)
```

**Key Configuration Options:**

- **Collection name**: Use a descriptive name (e.g., "PDFDocuments", "TechnicalManuals")
- **Properties**: Add all metadata you want to filter or display
  - `page_id`: Unique identifier for each page
  - `document_id`: Identifier for the source document
  - `page_number`: Page position within document
  - `title`: Document title or section header
- **Vector name**: `"colqwen"` indicates ColQwen2 embeddings
- **MUVERA encoding**: Optional compression (comment out for first iteration)
  - Use for large collections (>100k documents)
  - Provides ~4x compression with minimal quality loss

## Step 5: Index Documents with ColQwen2

### Batch Import Strategy

```python
import numpy as np

# Store images for later visualization (optional)
page_images = {}

with collection.batch.dynamic() as batch:
    for idx, document in enumerate(your_document_dataset):
        # Generate ColQwen2 multi-vector embedding
        embedding = embedder.embed_image(document["image"])

        # Convert tensor to list format for Weaviate
        # Shape: (num_patches, 128) -> list of 128-dim vectors
        embedding_list = embedding.cpu().float().numpy().tolist()

        # Store image reference for later visualization
        page_images[document["page_id"]] = document["image"]

        # Add object to batch
        batch.add_object(
            properties={
                "page_id": document["page_id"],
                "document_id": document["document_id"],
                "page_number": document["page_number"],
                "title": document.get("title", ""),
                # Add other properties from your dataset
            },
            vector={"colqwen": embedding_list}
        )

        # Progress tracking
        if idx % 25 == 0:
            print(f"Indexed {idx+1}/{len(your_document_dataset)} documents")

    # Ensure all batches are committed
    batch.flush()

# Clean up dataset if memory is limited
del your_document_dataset

print(f"Total documents indexed: {len(collection)}")
```

**Performance Tips:**

- **Batch size**: Weaviate automatically manages batch size with `dynamic()` mode
- **GPU memory**: Each ColQwen2 forward pass uses ~2-3 GB, process one image at a time
- **CPU fallback**: If GPU memory is limited, embeddings will automatically use CPU
- **Large datasets**: Process in chunks, delete intermediate variables to free memory
- **Image resolution**: Lower resolution = fewer patches = faster embedding + less storage

## Step 6: Implement Retrieval with ColQwen2

### Basic Query Function

ColQwen2 uses MaxSim (Maximum Similarity) scoring between query and document multi-vectors:

```python
from weaviate.classes.query import MetadataQuery

def search_documents(query_text, limit=3):
    """Search for documents using ColQwen2 embeddings.

    Args:
        query_text: Natural language query string
        limit: Number of results to return (default: 3)

    Returns:
        List of dicts with document properties, similarity scores, and images
    """
    # Generate ColQwen2 query embedding
    query_embedding = embedder.embed_text(query_text)

    # Search collection using multi-vector similarity
    response = collection.query.near_vector(
        near_vector=query_embedding.cpu().float().numpy(),
        target_vector="colqwen",
        limit=limit,
        return_metadata=MetadataQuery(distance=True),
    )

    # Process and format results
    results = []
    for i, obj in enumerate(response.objects):
        props = obj.properties
        # Distance is negative MaxSim score, so negate it
        maxsim_score = -obj.metadata.distance
        results.append({
            "rank": i + 1,
            "page_id": props["page_id"],
            "document_id": props["document_id"],
            "page_number": props["page_number"],
            "title": props["title"],
            "maxsim_score": maxsim_score,
            "image": page_images[props["page_id"]]
        })

    return results

# Example usage
query = "How does DeepSeek-V2 compare against the LLaMA family of LLMs?"
results = search_documents(query, limit=3)

for result in results:
    print(f"{result['rank']}) MaxSim: {result['maxsim_score']:.2f}, "
          f"Title: \"{result['title']}\", Page: {result['page_number']}")
```

**Query Parameters:**

- **`limit`**: Number of results (1-10 recommended, consider VLM memory limits)
- **`target_vector`**: Use `"colqwen"` to search ColQwen2 embeddings
- **`return_metadata`**: Include `distance=True` to get MaxSim scores
- **Filters**: Add `.where()` for metadata filtering (see Step 8)

**Understanding MaxSim Scores:**

- Higher scores = better matches (typically 15-30 for good matches)
- MaxSim computes maximum similarity between any query token and document patch
- Late-interaction allows fine-grained matching of specific concepts

## Step 7: Extend to Full RAG with Qwen2.5-VL

### About Qwen2.5-VL

Qwen2.5-VL is a vision language model that pairs well with ColQwen2:

- **License**: Apache 2.0 / Tongyi Qianwen (check model card)
- **Model Options**:
  - `Qwen/Qwen2.5-VL-3B-Instruct`: ~3 GB, good for limited hardware
  - `Qwen/Qwen2.5-VL-7B-Instruct`: ~7 GB, better quality
  - `Qwen/Qwen2.5-VL-72B-Instruct`: ~72 GB, highest quality
- **Capabilities**: Multimodal understanding (text + images), instruction following

**Alternative Options:**

- API-based VLMs (GPT-4V, Claude 3, Gemini): Easier setup, usage costs
- Other open-source VLMs (LLaVA, InternVL): Different quality/size tradeoffs

### Load Qwen2.5-VL Model

```python
import base64
from io import BytesIO
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# Load Qwen2.5-VL model
model_name = "Qwen/Qwen2.5-VL-3B-Instruct"  # Or use 7B/72B variants

qwen_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map=device,
    attn_implementation=attn_implementation,
)

# Load processor with min/max pixel settings
min_pixels = 256 * 28 * 28
max_pixels = 1280 * 28 * 28
qwen_processor = AutoProcessor.from_pretrained(
    model_name,
    min_pixels=min_pixels,
    max_pixels=max_pixels
)
```

### Implement Qwen2.5-VL Wrapper

```python
class Qwen2_5_VL:
    def __init__(self, model, processor):
        """Initialize with loaded Qwen2.5-VL model and processor."""
        self.model = model
        self.processor = processor

    def generate_answer(self, query, images, max_tokens=128):
        """Generate text response based on query and retrieved document images.

        Args:
            query: String text query
            images: List of PIL.Image objects from retrieval
            max_tokens: Maximum tokens to generate (default: 128)

        Returns:
            Generated text answer as string
        """
        # Convert PIL images to base64 strings
        content = []
        for img in images:
            buffer = BytesIO()
            img.save(buffer, format="jpeg")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            content.append({
                "type": "image",
                "image": f"data:image;base64,{img_base64}"
            })

        # Add text query after images
        content.append({"type": "text", "text": query})

        # Format as messages
        messages = [{"role": "user", "content": content}]

        # Apply chat template
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # Process vision inputs
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.model.device)

        # Generate response
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens
        )

        # Trim input tokens from output
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        # Decode and return
        return self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

# Instantiate the VLM
qwen_vlm = Qwen2_5_VL(qwen_model, qwen_processor)
```

### Complete RAG Pipeline

```python
def multimodal_rag(query, num_documents=3, max_tokens=128):
    """Complete multimodal RAG pipeline using ColQwen2 + Qwen2.5-VL.

    Args:
        query: Natural language question
        num_documents: Number of documents to retrieve (1-3 recommended)
        max_tokens: Maximum tokens for VLM response

    Returns:
        Dict with query, answer, sources, and metadata
    """
    # Step 1: Retrieve relevant documents using ColQwen2
    print(f"Searching for: {query}")
    retrieved_docs = search_documents(query, limit=num_documents)

    # Display retrieved sources
    print(f"\nRetrieved {len(retrieved_docs)} documents:")
    for doc in retrieved_docs:
        print(f"  - {doc['title']}, Page {doc['page_number']} "
              f"(MaxSim: {doc['maxsim_score']:.2f})")

    # Step 2: Extract images from results
    context_images = [doc["image"] for doc in retrieved_docs]

    # Step 3: Generate answer using Qwen2.5-VL
    print(f"\nGenerating answer...")
    answer = qwen_vlm.generate_answer(query, context_images, max_tokens=max_tokens)

    # Step 4: Return structured response
    return {
        "query": query,
        "answer": answer,
        "sources": retrieved_docs,
        "num_sources": len(retrieved_docs)
    }

# Example usage
query = "How does DeepSeek-V2 compare against the LLaMA family of LLMs?"
result = multimodal_rag(query, num_documents=1, max_tokens=128)

print(f"\nQuery: {result['query']}")
print(f"Answer: {result['answer']}")
print(f"\nBased on {result['num_sources']} source(s)")
```

**Memory Considerations:**

- **GPU Memory**: With 3B model + ColQwen2, expect ~8-10 GB total
- **Reduce `num_documents`**: If OOM errors occur, retrieve fewer documents (even 1 can work well)
- **Reduce `max_tokens`**: Shorter responses use less memory
- **Use CPU offloading**: Set `device_map="auto"` for automatic memory management

### Metadata Filtering

Add filters to narrow search scope by document properties:

```python
# Example: Filter by document type
response = collection.query.near_vector(
    near_vector=query_embedding.cpu().float().numpy(),
    target_vector="colqwen",
    limit=5,
    filters=wc.Filter.by_property("document_type").equal("research_paper"),
)

# Example: Filter by page range
response = collection.query.near_vector(
    near_vector=query_embedding.cpu().float().numpy(),
    target_vector="colqwen",
    limit=5,
    filters=wc.Filter.by_property("page_number").less_than(10),
)

# Example: Combine multiple filters
from weaviate.classes.query import Filter

response = collection.query.near_vector(
    near_vector=query_embedding.cpu().float().numpy(),
    target_vector="colqwen",
    limit=5,
    filters=(
        Filter.by_property("document_type").equal("research_paper") &
        Filter.by_property("page_number").less_than(10)
    ),
)
```

### Hybrid Search

Combine ColQwen2 vector search with BM25 keyword search:

```python
# Generate ColQwen2 embedding
query_embedding = embedder.embed_text(query_text)

# Hybrid search: vector + keyword
response = collection.query.hybrid(
    query=query_text,  # Used for BM25 keyword search
    vector=query_embedding.cpu().float().numpy(),  # ColQwen2 embeddings
    target_vector="colqwen",
    alpha=0.7,  # 0.0=keyword only, 0.5=balanced, 1.0=vector only
    limit=5,
)
```

**When to use hybrid search:**

- When exact keyword matches are important (e.g., searching for specific terms, IDs)
- To combine semantic understanding (ColQwen2) with exact text matching (BM25)
- Adjust `alpha` based on whether you prioritize semantic vs. keyword matching

### Response Citation

Include source attribution in generated answers:

```python
def generate_with_citations(query, retrieved_docs, max_tokens=256):
    """Generate answer with source citations.

    Args:
        query: User question
        retrieved_docs: List of documents from search_documents()
        max_tokens: Maximum response length

    Returns:
        Answer string with embedded citations
    """
    # Build source references
    sources_text = "\n".join([
        f"Source {i+1}: \"{doc['title']}\", Page {doc['page_number']}"
        for i, doc in enumerate(retrieved_docs)
    ])

    # Enhanced prompt with citation instructions
    enhanced_query = f"""{query}

Available sources:
{sources_text}

Instructions: Answer the question based on the provided document images.
Cite sources in your answer using [Source N] notation."""

    # Generate answer with citations
    answer = qwen_vlm.generate_answer(
        enhanced_query,
        [doc["image"] for doc in retrieved_docs],
        max_tokens=max_tokens
    )

    return answer, retrieved_docs

# Example usage
query = "What is the architecture of GPT-4?"
answer, sources = generate_with_citations(query, search_documents(query, limit=3))
print(f"Answer: {answer}\n")
print("Sources:")
for src in sources:
    print(f"  - {src['title']}, Page {src['page_number']}")
```

## Use Cases

This architecture is suitable for:

- **Academic research**: Search papers by concepts, figures, or tables
- **Technical documentation**: Find relevant diagrams and code snippets
- **Legal documents**: Retrieve contract clauses with visual context
- **Medical records**: Search imaging reports and scan results
- **E-commerce**: Visual product catalog search
- **Education**: Interactive textbook Q&A with diagrams

### Frontend

When the user explicitly asks for a frontend, use this reference as guideline:

- [Frontend Interface](frontend_interface.md): Build a Next.js frontend to interact with the Weaviate backend.
