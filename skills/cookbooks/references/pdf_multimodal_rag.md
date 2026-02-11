# Multi-vector RAG: Building Multimodal Document Search Systems With Weaviate

## Overview

This cookbook provides instructions for implementing a Multimodal Retrieval-Augmented Generation (RAG) system over PDF document collections using Weaviate Embeddings multimodal model for embeddings and Qwen2.5-VL for generation.

Weaviate Embeddings handles all embedding generation server-side — no local GPU or model downloads required. Simply upload document images as base64 blobs and Weaviate generates multi-vector embeddings automatically.

## Architecture

A multimodal RAG system consists of two main pipelines:

### 1. Ingestion Pipeline
- Documents (PDFs, images) are converted to page images
- Images are uploaded as base64 blobs to Weaviate
- Weaviate Embeddings generates multi-vector embeddings server-side using `ModernVBERT/colmodernvbert`
- Embeddings are stored in the vector index automatically

### 2. Query Pipeline
- Text queries are sent to Weaviate, which embeds them server-side
- Relevant documents are retrieved using similarity search (MaxSim)
- Retrieved document images are passed to a Vision Language Model (VLM) with the query
- The VLM generates a natural language response based on visual and textual context

## Prerequisites

Read first:
- Env/header mapping: [Environment Requirements](./environment-requirements.md)

Use `environment-requirements.md` mapping exactly.

### Requirements
- Weaviate Cloud instance (Weaviate Embeddings is cloud-only)
- Python 3.11 or higher
- `uv` package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- GPU with 3-7 GB memory only needed for local VLM generation (optional — can use API-based VLMs instead)

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
uv add weaviate-client
```

**Package breakdown:**
- `weaviate-client`: Python client for Weaviate vector database (v4.x) — Weaviate Embeddings handles all embedding generation

### Additional Dependencies (Install as Needed)

```bash
# For loading Hugging Face datasets
uv add datasets

# For PDF processing (pdf2image requires poppler to be installed!)
uv add pdf2image pillow

# For local VLM generation (optional — only if not using API-based VLMs)
uv add torch transformers qwen_vl_utils
```

## Step 2: Prepare Your Document Dataset

### Option A: Load Existing Dataset
If using a pre-existing dataset:
- Use Hugging Face `datasets` library
- Ensure dataset contains document images or can be converted to images
- Verify image format compatibility (JPEG, PNG)

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

## Step 3: Configure Weaviate Collection

### Weaviate Connection

```python
import os
import weaviate
from weaviate.classes.init import Auth

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
)
```

### Create Collection Schema

Define a collection with `multi2vec_weaviate` vectorizer for automatic multimodal embeddings:

```python
from weaviate.classes.config import Configure, Property, DataType

collection_name = "PDFDocuments"  # Use a descriptive name for your use case

collection = client.collections.create(
    name=collection_name,
    properties=[
        Property(name="doc_page", data_type=DataType.BLOB),
        Property(name="page_id", data_type=DataType.INT),
        Property(name="document_id", data_type=DataType.TEXT),
        Property(name="page_number", data_type=DataType.INT),
        Property(name="title", data_type=DataType.TEXT),
        # Add other metadata properties as needed
    ],
    vector_config=[
        Configure.MultiVectors.multi2vec_weaviate(
            name="doc_vector"
            image_field="doc_page",
            model="ModernVBERT/colmodernvbert",
            encoding=Configure.VectorIndex.MultiVector.Encoding.muvera(
                ksim=4,
                dprojections=16,
                repetitions=20,
            ),
        )
    ],
)
```

**Key Configuration Options:**
- **`doc_page`**: BLOB property that holds base64-encoded page images — the vectorizer reads this field
- **`image_field`**: Must match the BLOB property name (`"doc_page"`)
- **`model`**: `ModernVBERT/colmodernvbert` — 250M parameter late-interaction vision-language encoder, fine-tuned for visual document retrieval
- **MUVERA encoding**: Compresses multi-vectors into efficient single vectors while preserving retrieval quality
  - `ksim`: Number of similar vectors to consider (default: 4)
  - `dprojections`: Number of projection dimensions (default: 16)
  - `repetitions`: Number of encoding repetitions (default: 20)
- **Properties**: Add all metadata you want to filter or display

**Without MUVERA encoding** (uses more memory but preserves full multi-vector representation):
```python
vector_config=[
    Configure.MultiVectors.multi2vec_weaviate(
        name="doc_vector",
        image_field="doc_page",
        model="ModernVBERT/colmodernvbert",
    )
],
```

## Step 4: Index Documents

### Convert Images to Base64

```python
import base64
from io import BytesIO

def image_to_base64(image):
    """Convert a PIL Image to a base64-encoded string.

    Args:
        image: PIL.Image object

    Returns:
        Base64-encoded string of the JPEG image
    """
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
```

### Batch Import

Weaviate Embeddings generates embeddings server-side during import — no local model needed:

```python
# Store images for later VLM generation (optional)
page_images = {}

collection = client.collections.get(collection_name)

with collection.batch.dynamic() as batch:
    for idx, document in enumerate(your_document_dataset):
        # Convert image to base64
        img_base64 = image_to_base64(document["image"])

        # Store image reference for later VLM generation
        page_images[document["page_id"]] = document["image"]

        # Add object to batch — Weaviate generates embeddings automatically
        batch.add_object(
            properties={
                "doc_page": img_base64,
                "page_id": document["page_id"],
                "document_id": document["document_id"],
                "page_number": document["page_number"],
                "title": document.get("title", ""),
                # Add other properties from your dataset
            },
        )

        # Progress tracking
        if idx % 25 == 0:
            print(f"Indexed {idx+1}/{len(your_document_dataset)} documents")

# Clean up dataset if memory is limited
del your_document_dataset

print(f"Total documents indexed: {len(collection)}")
```

**Performance Tips:**
- **Batch size**: Weaviate automatically manages batch size with `dynamic()` mode
- **No local GPU needed**: Weaviate Embeddings runs server-side
- **Image format**: JPEG is recommended for smaller payload sizes
- **Large datasets**: Process in chunks, delete intermediate variables to free memory

## Step 5: Implement Retrieval

### Basic Query Function

Weaviate handles query embedding automatically — just pass text:

```python
from weaviate.classes.query import MetadataQuery

def search_documents(query_text, limit=3):
    """Search for documents using Weaviate Embeddings multimodal model.

    Args:
        query_text: Natural language query string
        limit: Number of results to return (default: 3)

    Returns:
        List of dicts with document properties, similarity scores, and images
    """
    collection = client.collections.get(collection_name)

    # Search — Weaviate embeds the query server-side
    response = collection.query.near_text(
        query=query_text,
        limit=limit,
        return_metadata=MetadataQuery(distance=True),
    )

    # Process and format results
    results = []
    for i, obj in enumerate(response.objects):
        props = obj.properties
        results.append({
            "rank": i + 1,
            "page_id": props["page_id"],
            "document_id": props["document_id"],
            "page_number": props["page_number"],
            "title": props["title"],
            "distance": obj.metadata.distance,
            "image": page_images[props["page_id"]],
        })

    return results

# Example usage
query = "How does DeepSeek-V2 compare against the LLaMA family of LLMs?"
results = search_documents(query, limit=3)

for result in results:
    print(f"{result['rank']}) Distance: {result['distance']:.4f}, "
          f"Title: \"{result['title']}\", Page: {result['page_number']}")
```

**Query Parameters:**
- **`limit`**: Number of results (1-10 recommended, consider VLM memory limits)
- **`return_metadata`**: Include `distance=True` to get similarity scores
- **Filters**: Add `filters=` for metadata filtering (see below)

**Accessing the image field in results:**
BLOB properties like `doc_page` are not returned by default when used as the image_field property of the multi2vec_weaviate vectorizer. If you need to access the stored image directly from search results (e.g., when `page_images` is not available), specify it explicitly with `return_properties`:
```python
response = collection.query.near_text(
    query=query_text,
    limit=limit,
    return_properties=["page_id", "document_id", "page_number", "title", "doc_page"],
    return_metadata=MetadataQuery(distance=True),
)
# Access the base64 image: obj.properties["doc_page"]
```

## Step 6: Extend to Full RAG with a Vision Language Model

### About Qwen2.5-VL

Qwen2.5-VL is a vision language model that can generate answers from retrieved document images:
- **License**: Apache 2.0 / Tongyi Qianwen (check model card)
- **Model Options**:
  - `Qwen/Qwen2.5-VL-3B-Instruct`: ~3 GB, good for limited hardware
  - `Qwen/Qwen2.5-VL-7B-Instruct`: ~7 GB, better quality
  - `Qwen/Qwen2.5-VL-72B-Instruct`: ~72 GB, highest quality

**Alternative Options:**
- API-based VLMs (GPT-4V, Claude 3, Gemini): Easier setup, usage costs, no local GPU needed
- Other open-source VLMs (LLaVA, InternVL): Different quality/size tradeoffs

### Load Qwen2.5-VL Model

```python
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from transformers.utils.import_utils import is_flash_attn_2_available
from qwen_vl_utils import process_vision_info

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
    """Complete multimodal RAG pipeline using Weaviate Embeddings + Qwen2.5-VL.

    Args:
        query: Natural language question
        num_documents: Number of documents to retrieve (1-3 recommended)
        max_tokens: Maximum tokens for VLM response

    Returns:
        Dict with query, answer, sources, and metadata
    """
    # Step 1: Retrieve relevant documents (Weaviate handles embedding)
    print(f"Searching for: {query}")
    retrieved_docs = search_documents(query, limit=num_documents)

    # Display retrieved sources
    print(f"\nRetrieved {len(retrieved_docs)} documents:")
    for doc in retrieved_docs:
        print(f"  - {doc['title']}, Page {doc['page_number']} "
              f"(Distance: {doc['distance']:.4f})")

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
- **Embedding**: No local GPU needed — Weaviate Embeddings runs server-side
- **VLM Generation**: With 3B model, expect ~3-7 GB GPU memory
- **Reduce `num_documents`**: If OOM errors occur, retrieve fewer documents (even 1 can work well)
- **Reduce `max_tokens`**: Shorter responses use less memory
- **Use CPU offloading**: Set `device_map="auto"` for automatic memory management
- **API-based VLMs**: Use GPT-4V, Claude 3, or Gemini to avoid local GPU requirements entirely

### Metadata Filtering

Add filters to narrow search scope by document properties:

```python
import weaviate.classes.config as wc

# Example: Filter by document ID
response = collection.query.near_text(
    query="query text",
    limit=5,
    filters=wc.Filter.by_property("document_id").equal("paper_123"),
)

# Example: Filter by page range
response = collection.query.near_text(
    query="query text",
    limit=5,
    filters=wc.Filter.by_property("page_number").less_than(10),
)

# Example: Combine multiple filters
from weaviate.classes.query import Filter

response = collection.query.near_text(
    query="query text",
    limit=5,
    filters=(
        Filter.by_property("document_id").equal("paper_123") &
        Filter.by_property("page_number").less_than(10)
    ),
)
```

### Hybrid Search

Combine vector search with BM25 keyword search:

```python
# Hybrid search: vector + keyword (Weaviate handles embedding)
response = collection.query.hybrid(
    query="query text",
    alpha=0.7,  # 0.0=keyword only, 0.5=balanced, 1.0=vector only
    limit=5,
)
```

**When to use hybrid search:**
- When exact keyword matches are important (e.g., searching for specific terms, IDs)
- To combine semantic understanding with exact text matching (BM25)
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
