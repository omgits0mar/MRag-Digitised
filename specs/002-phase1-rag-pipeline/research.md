# Research: Phase 1 — RAG Foundation Pipeline

**Branch**: `002-phase1-rag-pipeline` | **Date**: 2026-04-07

## R1: Natural Questions Dataset Format & Ingestion

**Decision**: Load the dataset from CSV/JSON using Pandas, with schema validation via Pydantic models at ingestion boundary.

**Rationale**: The Natural Questions dataset from Kaggle is distributed as CSV or simplified JSON. Pandas handles both formats efficiently with built-in dtype inference and missing-value detection. Pydantic validation at the boundary catches schema violations before data enters the pipeline.

**Alternatives considered**:
- Raw Python CSV reader: Too low-level, no dtype inference, poor Unicode handling
- Polars: Faster for large datasets but adds a new dependency with limited ecosystem benefit for ~300K rows
- Direct JSON streaming: Viable but Pandas provides better tabular operations for enrichment

## R2: Text Chunking Strategy

**Decision**: Sliding window with sentence-boundary alignment. Default chunk size 512 tokens, 50-token overlap. Use a simple sentence splitter based on punctuation + Unicode sentence boundaries.

**Rationale**: Sentence-boundary-aligned chunks preserve semantic coherence, which the constitution (Article II) requires. Token-based sizing (rather than character-based) ensures consistent information density per chunk. The sliding window with overlap prevents information loss at boundaries.

**Alternatives considered**:
- Fixed character-count chunks: Simpler but breaks mid-sentence, degrading retrieval quality
- Recursive text splitting (LangChain-style): Adds external dependency; the logic is straightforward enough to implement directly
- Semantic chunking (embedding-based): Too expensive for initial pass; can be added in Phase 2 as an optimization

## R3: Metadata Enrichment Approach

**Decision**: Rule-based classifiers for question type (regex + keyword patterns), TF-IDF with pre-defined category list for domain classification, heuristic difficulty scoring based on answer availability.

**Rationale**: Lightweight, deterministic, no ML model dependency. The constitution requires reproducibility (Article II). Heuristic classifiers provide adequate accuracy for metadata filtering without GPU requirements.

**Alternatives considered**:
- Zero-shot classification (LLM-based): High accuracy but requires API calls, breaking offline-capability requirement
- Fine-tuned classifier: Needs training data and GPU; overkill for metadata tagging
- Manual annotation: Not scalable for ~300K records

## R4: Multilingual Embedding Model

**Decision**: `paraphrase-multilingual-MiniLM-L12-v2` from Sentence Transformers. 384-dimensional embeddings, 50+ languages, ~120MB model size.

**Rationale**: Constitution (Article III) mandates multilingual from day one. This model balances quality, speed, and size — 384 dims is manageable for FAISS with ~300K vectors (~440MB index). It outperforms monolingual models on cross-lingual retrieval benchmarks while remaining CPU-feasible.

**Alternatives considered**:
- `all-MiniLM-L6-v2`: Faster but English-only — violates Article III
- `paraphrase-multilingual-mpnet-base-v2`: Better quality (768 dims) but ~2x the index size and slower inference; upgrade path for Phase 2 if needed
- OpenAI embeddings: High quality but requires API calls, violates offline-capable requirement

## R5: FAISS Index Type

**Decision**: `IndexFlatIP` (exact inner product search on L2-normalized vectors = cosine similarity).

**Rationale**: Constitution (Article IV) prioritizes accuracy over speed. For ~300K 384-dim vectors, exact search is feasible in <100ms on modern hardware. L2-normalization before indexing means inner product equals cosine similarity, avoiding the need for separate distance computation.

**Alternatives considered**:
- `IndexIVFFlat`: ~5-10x faster for >1M vectors, but introduces recall loss. Premature for 300K vectors.
- `IndexHNSW`: Excellent recall at high speed but higher memory footprint and more complex tuning. Reserve for scaling beyond 1M.
- `IndexFlatL2`: Works but inner product on normalized vectors is equivalent and aligns with how similarity is typically reported.

## R6: Metadata Storage Strategy

**Decision**: JSON-backed dictionary keyed by integer FAISS index ID. Stored as a single JSON file alongside the FAISS index.

**Rationale**: O(1) lookup by integer ID is the simplest approach that meets the constant-time access requirement. JSON is human-readable and debugging-friendly. For 300K records with ~10 fields each, the JSON file is ~50-100MB — fits in memory easily.

**Alternatives considered**:
- SQLite: More robust for larger datasets but adds complexity; not needed until Phase 3 (Feature 008)
- Shelve/pickle: Binary format, not human-readable, platform-dependent serialization issues
- Parquet: Better for columnar queries but overkill for key-value access pattern

## R7: Re-ranking Strategy

**Decision**: Weighted scoring combining cosine similarity with metadata relevance signals. Initial implementation uses a configurable linear combination: `score = alpha * cosine_sim + (1 - alpha) * metadata_boost`.

**Rationale**: Constitution (Article IV) explicitly states "raw cosine similarity alone is insufficient." A simple weighted combination provides a clear improvement over raw similarity while remaining interpretable and tunable. Metadata boost can factor in question-type match, domain relevance, and answer availability.

**Alternatives considered**:
- Cross-encoder re-ranking: High quality but requires additional model inference per result — too expensive for Phase 1
- BM25 hybrid: Effective but requires maintaining a separate keyword index
- Reciprocal Rank Fusion: Useful when combining multiple retrieval sources, but we have a single source in Phase 1

## R8: Data Export Format

**Decision**: JSON Lines (`.jsonl`) with deterministic 90/10 train/evaluation split using a fixed random seed.

**Rationale**: JSONL is streaming-friendly (one record per line), compatible with most ML tooling, and human-readable. The fixed seed ensures reproducibility per Article II. 90/10 split follows the project plan's evaluation requirements.

**Alternatives considered**:
- Parquet: More compact and faster to load but less human-readable for debugging
- CSV: Loses nested structure (chunks, metadata) without awkward flattening
- HDF5: Good for numerical data but overkill for text-heavy records

## R9: Batch Processing for Embeddings

**Decision**: Process embeddings in batches of 64 samples. Configurable via settings.

**Rationale**: Batch size 64 balances memory usage (~25MB per batch at 384 dims) with throughput. Sentence Transformers natively supports batched encoding. Progress logging per batch enables monitoring for the full ~300K record run.

**Alternatives considered**:
- Single-sample encoding: Extremely slow due to Python overhead per call
- Batch size 256+: Faster but may cause OOM on machines with <8GB RAM
- Dynamic batching: Over-engineering for a fixed pipeline; static batch size is sufficient
