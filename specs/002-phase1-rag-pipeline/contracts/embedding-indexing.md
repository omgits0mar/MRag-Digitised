# Contract: Embedding & Vector Indexing

**Module**: `src/mrag/embeddings/`

## Embedding Interface

### `EmbeddingEncoder(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2")`

Wrapper around Sentence Transformers for multilingual embedding generation.

### `EmbeddingEncoder.encode(texts: list[str], batch_size: int = 64) -> np.ndarray`

Generate L2-normalized embeddings for a batch of texts.

**Input**:
- `texts`: List of text strings to embed
- `batch_size`: Processing batch size (default 64)

**Output**: `np.ndarray` of shape `(len(texts), embedding_dim)`, dtype `float32`, L2-normalized

**Errors**:
- `EmbeddingError` if model fails to load or encode

**Guarantees**:
- All output vectors are L2-normalized (unit length)
- Consistent dimensionality across all calls
- Empty input returns empty array of shape `(0, embedding_dim)`

### `EmbeddingEncoder.encode_single(text: str) -> np.ndarray`

Generate embedding for a single text (convenience method for query embedding).

**Output**: `np.ndarray` of shape `(embedding_dim,)`, L2-normalized

---

## Indexer Interface

### `FAISSIndexer(dimension: int = 384, index_type: str = "Flat")`

FAISS index wrapper for vector storage and similarity search.

### `FAISSIndexer.build_index(vectors: np.ndarray) -> None`

Build the FAISS index from a matrix of vectors.

**Input**: `np.ndarray` of shape `(n, dimension)`, L2-normalized

**Errors**: `RetrievalError` if dimension mismatch

### `FAISSIndexer.search(query_vector: np.ndarray, top_k: int = 5) -> tuple[np.ndarray, np.ndarray]`

Search for nearest neighbors.

**Input**:
- `query_vector`: Shape `(dimension,)` or `(1, dimension)`, L2-normalized
- `top_k`: Number of results

**Output**: Tuple of `(scores, indices)` each of shape `(top_k,)`
- `scores`: Similarity scores (cosine similarity for normalized vectors)
- `indices`: Integer FAISS IDs

### `FAISSIndexer.save(path: str) -> None`

Persist index to disk.

### `FAISSIndexer.load(path: str) -> None`

Load index from disk.

**Errors**: `RetrievalError` if file not found or corrupted

---

## Metadata Store Interface

### `MetadataStore()`

Parallel metadata storage keyed by FAISS integer ID.

### `MetadataStore.add(faiss_id: int, metadata: MetadataEntry) -> None`

Add a metadata entry.

### `MetadataStore.get(faiss_id: int) -> MetadataEntry`

Retrieve metadata by FAISS ID.

**Errors**: `KeyError` if ID not found

### `MetadataStore.filter(field: str, value: str) -> list[int]`

Return FAISS IDs matching a metadata field value.

**Input**:
- `field`: Metadata field name (e.g., "domain", "question_type")
- `value`: Value to match

**Output**: List of matching FAISS integer IDs

### `MetadataStore.save(path: str) -> None` / `MetadataStore.load(path: str) -> None`

Persist/load metadata to/from JSON file.

---

## Embedding Pipeline Interface

### `run_embedding_pipeline(config: Settings, input_file: str) -> EmbeddingPipelineResult`

Orchestrate: load processed chunks → embed → index → save.

**Input**:
- `config`: Application settings
- `input_file`: Path to JSONL from data processing pipeline

**Output**: `EmbeddingPipelineResult` with statistics (chunks embedded, index size, time elapsed)

**Side effects**: Writes FAISS index (`.faiss`) and metadata (`.json`) to configured data directory
