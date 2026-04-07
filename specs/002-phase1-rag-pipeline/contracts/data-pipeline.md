# Contract: Data Processing Pipeline

**Module**: `src/mrag/data/`

## Ingestion Interface

### `load_dataset(file_path: str, file_format: str = "csv") -> list[RawRecord]`

Load and validate raw dataset from file.

**Input**:
- `file_path`: Path to the raw dataset file (CSV or JSON)
- `file_format`: One of `"csv"`, `"json"`

**Output**: List of validated `RawRecord` objects

**Errors**:
- `DataProcessingError` if file not found, unreadable, or schema validation fails on all records
- Malformed individual records are logged and skipped (not raised)

**Side effects**: Logs summary of loaded/skipped record counts

---

## Chunking Interface

### `TextChunker(chunk_size: int = 512, chunk_overlap: int = 50)`

Configurable text chunker with sentence-boundary alignment.

### `TextChunker.chunk(text: str, doc_id: str) -> list[TextChunk]`

Split text into overlapping chunks.

**Input**:
- `text`: Source text to chunk
- `doc_id`: Parent document ID for chunk ID generation

**Output**: List of `TextChunk` objects (minimum 1 element)

**Guarantees**:
- Deterministic: identical input always produces identical output
- Sentence boundaries preserved (no mid-sentence splits)
- Short text (below chunk_size) returns a single chunk
- Unicode-safe: handles all UTF-8 text correctly

---

## Enrichment Interface

### `enrich(question: str, answer_short: str | None, answer_long: str) -> DocumentMetadata`

Classify and enrich a question-answer pair.

**Input**:
- `question`: Question text
- `answer_short`: Short answer (may be None)
- `answer_long`: Long answer text

**Output**: `DocumentMetadata` with all fields populated

**Guarantees**:
- All required fields are non-null
- Classification is deterministic
- Unknown patterns default to `"unknown"` question_type

---

## Export Interface

### `export_jsonl(documents: list[ProcessedDocument], output_dir: str, split_ratio: float = 0.9, seed: int = 42) -> tuple[str, str]`

Export processed documents to JSONL with train/eval split.

**Input**:
- `documents`: Fully processed documents
- `output_dir`: Directory for output files
- `split_ratio`: Fraction for training set (default 0.9)
- `seed`: Random seed for reproducible split

**Output**: Tuple of (train_file_path, eval_file_path)

**Guarantees**:
- Deterministic split with fixed seed
- All fields and metadata preserved in output
- One JSON object per line

---

## Pipeline Interface

### `run_pipeline(config: Settings) -> PipelineResult`

Orchestrate the full data processing pipeline: ingest → chunk → enrich → export.

**Input**: Application settings (contains file paths, chunk config, etc.)

**Output**: `PipelineResult` with statistics (records processed, skipped, chunks created, etc.)

**Errors**: `DataProcessingError` for unrecoverable failures

**Side effects**: Writes JSONL files to configured output directory, logs progress at each stage
