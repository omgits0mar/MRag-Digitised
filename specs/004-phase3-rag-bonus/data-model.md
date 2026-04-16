# Data Model: Phase 3 RAG Bonus

**Branch**: `004-phase3-rag-bonus` | **Date**: 2026-04-09

## Entity Diagram

```
                         ┌─────────────────────┐
                         │   HTTP Request       │
                         │   (QuestionRequest)  │
                         └──────────┬──────────┘
                                    │ validates
                                    ▼
                         ┌─────────────────────┐
                         │  QuestionResponse    │◄──── wraps GeneratedResponse (Phase 2)
                         └──────────┬──────────┘
                                    │ persists
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                           │
│                                                                     │
│  QueryRecord ──N:1──► ConversationTurn (via conversation_id)        │
│  ConversationTurn ──N:1──► Conversation (by conversation_id index)  │
│  AnalyticsSnapshot ── standalone aggregate                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        EVALUATION LAYER                             │
│                                                                     │
│  EvaluationDataset ──1:N──► EvaluationQuery                         │
│  EvaluationQuery ──1:1──► RetrievalMetrics (per query)              │
│  EvaluationQuery ──1:1──► ResponseQualityMetrics (per query)        │
│  EvaluationReport ──1:1──► RetrievalMetrics (aggregate)             │
│  EvaluationReport ──1:1──► ResponseQualityMetrics (aggregate)       │
│  EvaluationReport ──1:1──► BenchmarkResult                          │
│  EvaluationReport ──0:1──► BaselineComparison                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Entities (Pydantic — `src/mrag/api/schemas.py`)

### QuestionRequest

Incoming payload for `POST /ask-question`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| question | str | min_length=1, max_length=2000 | The user's question text |
| conversation_id | str \| None | optional, max_length=64 | Ties this question to a conversation for multi-turn context |
| expand | bool | default=True | Whether to run query expansion |
| temperature | float | default=0.1, ge=0, le=2 | LLM sampling temperature |
| max_tokens | int | default=1024, ge=1, le=4096 | Max LLM response tokens |

### QuestionResponse

Outgoing payload for `POST /ask-question`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| answer | str | | Generated answer text |
| confidence_score | float | 0.0–1.0 | Confidence of the generated answer |
| is_fallback | bool | | True if a fallback response was returned |
| sources | list[SourceResponse] | | Cited passages |
| response_time_ms | float | >= 0 | Total end-to-end latency |
| conversation_id | str \| None | | Echo back (or newly assigned) conversation_id |

### SourceResponse

A single cited passage within `QuestionResponse.sources`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| chunk_id | str | | Unique chunk identifier |
| doc_id | str | | Parent document identifier |
| text | str | | Passage excerpt text |
| relevance_score | float | 0.0–1.0 | Retrieval relevance score |

### HealthResponse

Outgoing payload for `GET /health`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| status | str | one of: "healthy", "degraded", "not_ready" | Overall service status |
| vector_store | str | one of: "loaded", "not_loaded" | FAISS index readiness |
| llm_provider | str | one of: "reachable", "unreachable" | LLM API liveness (cached timestamp check) |
| database | str | one of: "connected", "disconnected" | Persistence store connectivity |
| uptime_seconds | float | >= 0 | Seconds since service startup |
| persistence_failure_count | int | >= 0 | Cumulative failed persistence writes since startup |

### EvaluateRequest

Incoming payload for `POST /evaluate`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| dataset_path | str \| None | optional | Path to evaluation dataset; defaults to `Settings.eval_heldout_path` |
| k_values | list[int] \| None | optional, each >= 1 | K values for retrieval metrics; defaults to `Settings.eval_k_values` |
| generate_report | bool | default=True | Whether to produce the HTML report artifact |
| compare_baseline | bool | default=True | Whether to compare against baseline metrics |

### EvaluateResponse

Outgoing payload for `POST /evaluate`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| retrieval | dict[str, float] | | Retrieval metrics (precision@K, recall@K, MRR, MAP) |
| response_quality | dict[str, float] | | BLEU, ROUGE-1, ROUGE-2, ROUGE-L |
| benchmark | dict[str, float] | | p50_ms, p95_ms, p99_ms, qps |
| regressions | list[RegressionFlag] | | List of metrics that regressed vs baseline |
| report_path | str \| None | | Filesystem path to generated HTML report, if requested |
| total_queries | int | | Number of evaluation queries processed |

### RegressionFlag

A single metric regression entry within `EvaluateResponse.regressions`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| metric | str | | Metric name (e.g., "precision_at_5") |
| baseline_value | float | | Value from the baseline file |
| current_value | float | | Value from this evaluation run |
| delta_pct | float | | Percentage change (negative = regression) |

### AnalyticsResponse

Outgoing payload for `GET /analytics`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| total_queries | int | >= 0 | Total queries in the window |
| avg_latency_ms | float | >= 0 | Mean total_time_ms |
| cache_hit_rate | float | 0.0–1.0 | Proportion of cache hits |
| top_domains | list[str] | max_length=10 | Most frequent query topics |
| queries_per_day | dict[str, int] | | Date string → count |

### ErrorEnvelope

Consistent error response for all failure modes.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| error | str | | Error code / category |
| detail | str | | Human-readable explanation |
| status_code | int | 400–599 | HTTP status code |

---

## Persistence Entities (SQLAlchemy ORM — `src/mrag/db/models.py`)

### QueryRecord

Persists every question-answer exchange.

| Column | SQL Type | Constraints | Description |
|--------|----------|-------------|-------------|
| id | Integer | PK, autoincrement | Row identifier |
| query_text | Text | NOT NULL | User's question |
| response_text | Text | NOT NULL | Generated answer |
| confidence_score | Float | NOT NULL | Answer confidence (0.0–1.0) |
| is_fallback | Boolean | NOT NULL, default=False | Whether fallback was returned |
| embedding_time_ms | Float | nullable | Embedding stage latency |
| search_time_ms | Float | nullable | Search stage latency |
| llm_time_ms | Float | nullable | LLM generation latency |
| total_time_ms | Float | NOT NULL | End-to-end latency |
| cache_hit | Boolean | NOT NULL, default=False | Whether response was cached |
| conversation_id | String(64) | nullable, indexed | Links to a conversation |
| error_indicator | String(255) | nullable | If persistence saw a degraded state, reason stored here |
| created_at | DateTime | NOT NULL, default=utcnow, indexed | Row creation timestamp |

**Indexes**: `ix_queryrecord_created_at` on `created_at`; `ix_queryrecord_conversation_id` on `conversation_id`.

### ConversationTurn

Tracks individual turns within a multi-turn conversation.

| Column | SQL Type | Constraints | Description |
|--------|----------|-------------|-------------|
| id | Integer | PK, autoincrement | Row identifier |
| conversation_id | String(64) | NOT NULL, indexed | Conversation grouping key |
| turn_number | Integer | NOT NULL | Sequential turn within conversation (1-based) |
| query_text | Text | NOT NULL | User's question this turn |
| response_text | Text | NOT NULL | System's answer this turn |
| created_at | DateTime | NOT NULL, default=utcnow | Turn creation timestamp |

**Indexes**: Compound index `ix_convturn_cid_turn` on `(conversation_id, turn_number DESC)` for efficient recent-turn retrieval.

### AnalyticsSnapshot

Pre-computed or on-demand analytics aggregation over a time period.

| Column | SQL Type | Constraints | Description |
|--------|----------|-------------|-------------|
| id | Integer | PK, autoincrement | Row identifier |
| period_start | DateTime | NOT NULL | Window start (inclusive) |
| period_end | DateTime | NOT NULL | Window end (exclusive) |
| total_queries | Integer | NOT NULL | Query count in window |
| avg_latency_ms | Float | NOT NULL | Mean total_time_ms in window |
| cache_hit_rate | Float | NOT NULL | Proportion of cache_hit=True |
| top_domains_json | Text | nullable | JSON-encoded top-domain list |
| created_at | DateTime | NOT NULL, default=utcnow | Snapshot creation timestamp |

**Note**: AnalyticsSnapshot is optionally materialized for historical tracking. Real-time analytics can be computed on-the-fly from `QueryRecord` aggregation queries.

---

## Evaluation Entities (Pydantic — `src/mrag/evaluation/models.py`)

### EvaluationQuery

A single query in the held-out evaluation dataset. Derived from Phase 1 `ProcessedDocument` records (produced by the 90/10 deterministic split of `Natural-Questions-Filtered.csv`).

| Field | Type | Constraints | Source (from ProcessedDocument) | Description |
|-------|------|-------------|--------------------------------|-------------|
| query_id | str | unique within dataset | `doc.doc_id` | Identifier for this evaluation query |
| question | str | min_length=1 | `doc.question` | The question text |
| relevant_chunk_ids | set[str] | | `{chunk.chunk_id for chunk in doc.chunks}` | Set of chunk IDs known to be relevant |
| reference_answer | str \| None | nullable | `doc.answer_short` | Ground-truth short answer (for BLEU/ROUGE) |

### EvaluationDataset

Container for the held-out evaluation set. Default source: `data/processed/eval.jsonl` (Phase 1 output).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| name | str | | Dataset identifier (e.g., "nq_heldout_v1") |
| queries | list[EvaluationQuery] | min_length=1 | List of evaluation queries |
| created_at | str | ISO 8601 | When the dataset was loaded |

### RetrievalMetrics

Computed retrieval quality metrics for a run.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| precision_at_k | dict[int, float] | keys are K values | Precision@K for each K |
| recall_at_k | dict[int, float] | keys are K values | Recall@K for each K |
| mrr | float | 0.0–1.0 | Mean reciprocal rank |
| map | float | 0.0–1.0 | Mean average precision |
| num_queries | int | >= 1 | Number of queries evaluated |

### ResponseQualityMetrics

Computed response quality scores for a run.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| bleu | float | 0.0–1.0 | Corpus-level BLEU (normalized from sacrebleu 0–100) |
| rouge_1 | float | 0.0–1.0 | ROUGE-1 fmeasure (aggregate) |
| rouge_2 | float | 0.0–1.0 | ROUGE-2 fmeasure (aggregate) |
| rouge_l | float | 0.0–1.0 | ROUGE-L fmeasure (aggregate) |
| num_pairs | int | >= 1 | Number of (predicted, reference) pairs evaluated |

### BenchmarkResult

Latency and throughput benchmarks for a run.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| p50_ms | float | >= 0 | 50th percentile total latency |
| p95_ms | float | >= 0 | 95th percentile total latency |
| p99_ms | float | >= 0 | 99th percentile total latency |
| qps | float | >= 0 | Queries per second throughput |
| num_queries | int | >= 1 | Number of benchmark queries processed |
| per_stage | dict[str, dict[str, float]] | | Per-stage p50/p95/p99 (stage → {"p50": ..., "p95": ..., "p99": ...}) |

### BaselineComparison

Result of comparing current metrics against a prior baseline.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| baseline_generated_at | str | ISO 8601 | When the baseline was produced |
| threshold_pct | float | 0.0–1.0 | Regression threshold applied |
| deltas | list[RegressionFlag] | | Per-metric delta and pass/regress indicator |
| has_regressions | bool | | True if any metric regressed beyond threshold |

### EvaluationReport

Top-level aggregation combining all evaluation results.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| generated_at | str | ISO 8601 | Report generation timestamp |
| mrag_version | str | | Application version from settings |
| dataset_name | str | | Name of the evaluation dataset used |
| retrieval | RetrievalMetrics | | Retrieval metric results |
| response_quality | ResponseQualityMetrics | | Response quality metric results |
| benchmark | BenchmarkResult | | Latency/throughput results |
| baseline_comparison | BaselineComparison \| None | nullable | Baseline comparison, if a baseline file existed |
| report_path | str \| None | nullable | Path to the generated HTML report file |

---

## State Transitions

### API Request Lifecycle

```
RECEIVED → VALIDATED → PIPELINE_PROCESSING → RESPONSE_READY → PERSISTING → RETURNED
                                                                    │
                                                                    └─ (on failure) → PERSIST_FAILED → RETURNED (response still valid)
```

### Conversation Turn Lifecycle

```
NEW_TURN → CONTEXT_LOADED (prior turns fetched) → PIPELINE_PROCESSING → TURN_PERSISTED
```

### Evaluation Run Lifecycle

```
DATASET_LOADED → RETRIEVAL_EVAL → RESPONSE_EVAL → BENCHMARK → BASELINE_COMPARE → REPORT_GENERATED → COMPLETE
```

### Health Probe Lifecycle

```
PROBE_RECEIVED → CHECK_VECTOR_STORE → CHECK_LLM_TIMESTAMP → CHECK_DB_SELECT1 → COMPUTE_UPTIME → RETURNED
```

---

## Relationships to Phase 1/2 Entities

- **Source data**: `Natural-Questions-Filtered.csv` (86,212 rows; columns: `question`, `short_answers`, `long_answers`) → Phase 1 data pipeline → `data/processed/train.jsonl` (90%) + `data/processed/eval.jsonl` (10% held-out)
- `EvaluationQuery` is derived from `ProcessedDocument` (Phase 1): `doc_id` → `query_id`, `question` → `question`, chunk IDs → `relevant_chunk_ids`, `answer_short` → `reference_answer`
- `EvaluationQuery.relevant_chunk_ids` are the FAISS chunk IDs from the Phase 1 vector store — the chunks belonging to a document ARE the ground-truth relevant passages for that question
- `QuestionResponse` wraps `GeneratedResponse` (Phase 2) — maps `answer`, `confidence_score`, `sources` fields from the pipeline output to the API schema
- `QuestionResponse.sources[*]` maps from `SourceCitation` (Phase 2): `chunk_id` → `chunk_id`, `doc_id` → `doc_id`, `chunk_text` → `text`, `relevance_score` → `relevance_score`
- `QueryRecord` latency fields map from `RequestMetrics` (Phase 2): `preprocessing_time_ms` is omitted from DB (not actionable for operators), `embedding_time_ms`, `search_time_ms`, `llm_time_ms`, `total_time_ms`, `cache_hit` are persisted directly
- `EvaluationRunner` consumes `MRAGPipeline` (Phase 2) as its pipeline parameter — evaluation exercises the exact same retrieval + generation path that the API uses
