# Quickstart: Phase 1 — RAG Foundation Pipeline

**Branch**: `002-phase1-rag-pipeline` | **Date**: 2026-04-07

## Prerequisites

- Python 3.10+ installed
- Project foundation (Feature 000) complete: `make install && make test && make lint` passes
- Natural Questions dataset downloaded (CSV format) into `data/raw/`

## Setup

```bash
# Ensure dependencies are installed (already done in Feature 000)
make install

# Copy and configure environment
cp .env.example .env
# Edit .env — set DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL_NAME as needed
```

## Running the Data Pipeline

```bash
# Process the dataset: ingest → chunk → enrich → export
python -m mrag.data.pipeline

# Output:
#   data/processed/train.jsonl    (90% of records)
#   data/processed/eval.jsonl     (10% of records)
```

## Running the Embedding Pipeline

```bash
# Embed all chunks and build FAISS index
python -m mrag.embeddings.pipeline

# Output:
#   data/processed/index.faiss       (vector index)
#   data/processed/metadata.json     (parallel metadata store)
```

## Running a Retrieval Query

```python
from mrag.config import get_settings
from mrag.embeddings.encoder import EmbeddingEncoder
from mrag.embeddings.indexer import FAISSIndexer
from mrag.embeddings.metadata_store import MetadataStore
from mrag.retrieval.retriever import RetrieverService
from mrag.retrieval.models import RetrievalRequest

settings = get_settings()

# Load components
encoder = EmbeddingEncoder(model_name=settings.embedding_model_name)
indexer = FAISSIndexer(dimension=settings.embedding_dimension)
indexer.load("data/processed/index.faiss")
metadata_store = MetadataStore()
metadata_store.load("data/processed/metadata.json")

# Create retriever
retriever = RetrieverService(encoder=encoder, indexer=indexer, metadata_store=metadata_store)

# Query
request = RetrievalRequest(query="What is photosynthesis?", top_k=5)
results = retriever.retrieve(request)

for r in results:
    print(f"[{r.relevance_score:.3f}] {r.chunk_text[:100]}...")
    print(f"  Domain: {r.domain}, Type: {r.question_type}")
```

## Running Tests

```bash
# All tests
make test

# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Specific module tests
python -m pytest tests/unit/test_chunking.py -v
python -m pytest tests/unit/test_encoder.py -v
python -m pytest tests/unit/test_retriever.py -v
```

## Key Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `CHUNK_SIZE` | 512 | Tokens per chunk |
| `CHUNK_OVERLAP` | 50 | Token overlap between chunks |
| `EMBEDDING_MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` | Sentence Transformer model |
| `EMBEDDING_DIMENSION` | 384 | Must match model output |
| `TOP_K` | 5 | Default retrieval result count |
| `FAISS_INDEX_TYPE` | `Flat` | FAISS index type (Flat/IVF/HNSW) |
| `DATA_DIR` | `data` | Base data directory |

## File Structure After Phase 1

```
data/
├── raw/
│   └── natural_questions.csv    # Downloaded dataset
├── processed/
│   ├── train.jsonl              # Training split (90%)
│   ├── eval.jsonl               # Evaluation split (10%)
│   ├── index.faiss              # FAISS vector index
│   └── metadata.json            # Parallel metadata store
└── evaluation/                  # Reserved for Phase 3

src/mrag/
├── data/
│   ├── __init__.py
│   ├── models.py                # ProcessedDocument, TextChunk, DocumentMetadata
│   ├── ingestion.py             # Dataset loading and validation
│   ├── chunking.py              # TextChunker class
│   ├── enrichment.py            # Question type, domain, difficulty classifiers
│   ├── export.py                # JSONL export and train/eval split
│   └── pipeline.py              # Data processing orchestration
├── embeddings/
│   ├── __init__.py
│   ├── encoder.py               # EmbeddingEncoder (Sentence Transformers wrapper)
│   ├── indexer.py               # FAISSIndexer (build/search/save/load)
│   ├── metadata_store.py        # MetadataStore (JSON-backed dict)
│   └── pipeline.py              # Embedding pipeline orchestration
└── retrieval/
    ├── __init__.py
    ├── models.py                # RetrievalRequest, RetrievalResult
    ├── ranking.py               # Re-ranking and scoring
    └── retriever.py             # RetrieverService
```
