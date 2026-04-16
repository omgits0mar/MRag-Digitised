# Research: Phase 3 RAG Bonus

**Branch**: `004-phase3-rag-bonus` | **Date**: 2026-04-09

This document resolves every technical unknown flagged in `plan.md` before Phase 1 design. Each entry follows the Decision / Rationale / Alternatives format.

---

## R1: FastAPI Lifespan Pattern for Heavy Resource Loading

**Decision**: Use FastAPI's `@asynccontextmanager` lifespan handler to construct all Phase 1/2 services once at startup and attach them to `app.state`. Routes access them via dependency injection functions that read from `app.state`.

**Rationale**: The MRAG pipeline loads non-trivial resources: a sentence-transformers model (~120 MB), a FAISS index (hundreds of MB), a Jinja2 environment, and an async LLM client with a keep-alive connection pool. Loading these per-request is infeasible. FastAPI's `lifespan` handler is the framework-blessed mechanism for startup/shutdown hooks in the modern (0.93+) API. Per-request DI via `Depends()` then reads from `app.state` with zero cost.

**Alternatives considered**:
- **Module-level globals**: Breaks testability (can't reset between tests), couples import order to resource readiness.
- **Deprecated `@app.on_event("startup")`**: Deprecated in FastAPI 0.93 in favour of lifespan. Avoid for forward compatibility.
- **Lazy loading on first request**: First request would time out; fails fast is preferred per FR-008.

**Pattern**:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.pipeline = await build_mrag_pipeline(settings)
    app.state.db_engine = create_async_engine(settings.database_url.get_secret_value())
    app.state.evaluator = EvaluationRunner(pipeline=app.state.pipeline)
    app.state.startup_ts = time.time()
    yield
    await app.state.pipeline.aclose()
    await app.state.db_engine.dispose()
```

Tests use `TestClient(app)` which triggers the lifespan automatically, or `AsyncClient(app=app)` wrapped in `LifespanManager` for finer control.

---

## R2: Async SQLAlchemy 2.0 for SQLite Dev / MySQL Prod via Same Code Path

**Decision**: Use `sqlalchemy.ext.asyncio.create_async_engine` with a URL-driven driver selection. Local dev uses `sqlite+aiosqlite:///mrag.db` (default in `Settings.database_url`). Production uses `mysql+aiomysql://user:pw@host/mrag` via the same code path — only the `DATABASE_URL` env var changes.

**Rationale**: SQLAlchemy 2.0's async API is driver-agnostic for the async variants. The repository code talks to `AsyncSession` and never touches driver-specific types. `aiosqlite` is a tiny (~50 KB) pure-Python dep suitable for dev and CI. `aiomysql` is added as an optional extra (not installed by default) so the core distribution stays lean.

**Alternatives considered**:
- **Sync SQLAlchemy with thread executors**: Forces every DB call through `run_in_executor`. Slower, more code, defeats the point of async FastAPI.
- **Two separate code paths (sync SQLite + async MySQL)**: Doubles test surface, makes persistence-isolation logic diverge between environments.
- **Raw `aiosqlite`/`aiomysql` without SQLAlchemy**: Skips Article VII's explicit SQLAlchemy mandate.

**Schema creation strategy**: `await conn.run_sync(Base.metadata.create_all)` inside the lifespan startup. Idempotent — creates tables only if absent. Phase 3 explicitly treats Alembic migrations as optional; production MySQL bootstrap is a one-shot DDL script, not a migration chain.

**URL configuration**:

```python
# .env (dev)
DATABASE_URL=sqlite+aiosqlite:///mrag.db

# .env (prod)
DATABASE_URL=mysql+aiomysql://mrag_user:***@db.internal:3306/mrag?charset=utf8mb4
```

---

## R3: Persistence Failure Isolation — the `safe_persist` Wrapper

**Decision**: Introduce a `safe_persist(coro, *, operation: str) -> None` utility that awaits a persistence coroutine inside a try/except that catches `SQLAlchemyError` and any `Exception`, logs via structlog with `operation`, `error_type`, and `error_detail` fields, and returns without re-raising. The API route calls `await safe_persist(query_repo.create(...), operation="persist_query")`.

**Rationale**: FR-012 and SC-011 require that a persistence outage never blocks the API caller. The safest pattern is a dedicated wrapper so the policy is enforced in exactly one place — routes cannot accidentally leak a persistence exception by forgetting to wrap it. This also makes the degraded state observable: every caller logs the same structured event, so an operator can build a "persistence_failures_total" counter trivially from logs.

**Alternatives considered**:
- **Try/except inline in each route**: Duplicates policy, easy to forget, inconsistent logging fields.
- **Middleware-level exception handler**: Middleware runs after the route handler, can't distinguish "persistence failed but response is valid" from "real 500".
- **Background task queue**: Overkill for Phase 3; adds Celery/RQ as a new infrastructure dep.

**Observability**: The wrapper increments a module-level `persistence_failure_count` that the `/health` endpoint reports so operators can see degraded-but-serving state without shipping a separate metrics backend.

---

## R4: Retrieval Metrics — Custom Implementations Validated Against scikit-learn

**Decision**: Implement `precision_at_k`, `recall_at_k`, `mean_reciprocal_rank`, and `mean_average_precision` as pure-Python functions in `src/mrag/evaluation/retrieval_metrics.py`. Validate correctness in unit tests by asserting equivalence with `sklearn.metrics.average_precision_score` on known-answer fixtures where sklearn has a reference, and by asserting exact values against hand-computed cases otherwise.

**Rationale**: scikit-learn does not ship a direct `precision@K` or `recall@K` for ranked-retrieval evaluation (its `precision_score`/`recall_score` target classification, not ranking). It does ship `average_precision_score` which matches MAP for the binary-relevance case — so MAP has a sklearn oracle. For precision@K / recall@K / MRR we write the straightforward definitions and prove correctness with known-answer fixtures (e.g., a 10-query fixture where each metric has a pre-computed value by hand). This is the Article VI + FR-021 discipline.

**Alternatives considered**:
- **`pytrec_eval`**: Adds a compiled dependency (libtrec_eval). Overkill for four metrics.
- **`ranx`**: Nice library but adds numpy-heavy deps and ties us to its `Qrels` format.
- **Rolling our own with no oracle**: Violates FR-021 — cannot prove correctness by test.

**Function signatures** (finalized in `contracts/evaluation_runner.md`):

```python
def precision_at_k(predicted: list[str], relevant: set[str], k: int) -> float
def recall_at_k(predicted: list[str], relevant: set[str], k: int) -> float
def mean_reciprocal_rank(rankings: list[list[str]], relevants: list[set[str]]) -> float
def mean_average_precision(rankings: list[list[str]], relevants: list[set[str]]) -> float
```

Inputs are lists of document/chunk IDs; `relevant` is a set of IDs known to be relevant to the query. The held-out dataset is loaded from `data/processed/eval.jsonl` (the 10% eval split of `Natural-Questions-Filtered.csv` produced by Phase 1). Each `ProcessedDocument` carries its own chunk IDs — these serve as the ground-truth relevant set, since in the Natural Questions dataset, the answer passage IS the ground truth. `answer_short` serves as the reference answer for BLEU/ROUGE evaluation.

---

## R5: BLEU Library Choice — `sacrebleu` over `nltk`

**Decision**: Use `sacrebleu` for BLEU computation.

**Rationale**: `sacrebleu` is the community-standard BLEU implementation (used in WMT evaluation). It has deterministic tokenization, no corpus download step, and a clean single-entry API (`sacrebleu.corpus_bleu(hypotheses, [references])`). `nltk.translate.bleu_score` requires downloading NLTK data at first use (`punkt`, etc.), has multiple tokenization gotchas, and is more prone to version drift in scoring conventions.

**Alternatives considered**:
- **`nltk.translate.bleu_score`**: Requires `nltk.download('punkt')` on first use — brittle in CI and in sandboxed deployments. Also has a smoothing-function pitfall for short references.
- **Custom implementation**: Violates FR-021 (needs a trustworthy oracle for correctness).
- **Hugging Face `evaluate`**: Large dependency footprint, network-gated on first use to download metric scripts.

**Usage shape**:

```python
import sacrebleu
result = sacrebleu.corpus_bleu(predicted_answers, [reference_answers])
bleu_score = result.score / 100  # sacrebleu returns 0–100, we normalize to 0–1
```

Note: the normalized 0–1 form matches the ROUGE output range so the report can present all text metrics on the same scale.

---

## R6: ROUGE Library Choice — Google's `rouge-score`

**Decision**: Use Google's `rouge-score` for ROUGE-1, ROUGE-2, and ROUGE-L.

**Rationale**: Google's `rouge-score` is the reference implementation backing the RougeL Summarization papers. It handles tokenization and stemming options consistently and reports `precision / recall / fmeasure` per metric. It's the implementation cited by all modern summarization benchmarks.

**Alternatives considered**:
- **`py-rouge`**: Older, less-maintained, slightly different tokenization.
- **`rouge`** (original PyPI package): Abandoned.
- **Hugging Face `evaluate`**: Same network/dependency concerns as BLEU above.

**Usage shape**:

```python
from rouge_score.rouge_scorer import RougeScorer
scorer = RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
scores = scorer.score(reference, prediction)
# scores["rouge1"].fmeasure → float in 0–1
```

---

## R7: Self-Contained HTML Report via matplotlib + Jinja2

**Decision**: Generate evaluation reports as a single self-contained HTML file. matplotlib renders charts to PNG in-memory, encodes them as base64, and embeds them directly into an `<img src="data:image/png;base64,...">` tag in a Jinja2 template (`prompts/templates/report.html.j2`). The final artifact is one `.html` file with no external assets — it opens in any browser, can be emailed, and requires no server to view.

**Rationale**: The spec (SC-009) requires "a single human-readable file containing all metrics and at least three charts." Self-contained HTML is the simplest way to hit that: Jinja2 is already a project dep, matplotlib is widely installed, base64 embedding keeps everything in one file. PDF generation is more complex (would need WeasyPrint or wkhtmltopdf), and the single-file HTML format is equivalent for stakeholder sharing.

**Alternatives considered**:
- **Static HTML + separate image files**: Violates "single file" requirement, awkward to email or archive.
- **PDF via WeasyPrint**: Extra toolchain dependency, slower, less readable in diff review.
- **Jupyter notebook export**: Adds jupyter as a dep, mixes code and output.
- **Plotly/Bokeh interactive charts**: Larger JS payloads, overkill for reproducible benchmark reports.

**Charts produced**:
1. **Precision vs K** — line chart, one series per run (current vs baseline)
2. **Latency distribution** — histogram of total_time_ms across benchmark workload
3. **Score histogram** — distribution of ROUGE-L fmeasures across the eval set

**Template structure** (abridged):

```jinja
<!DOCTYPE html>
<title>MRAG Evaluation Report — {{ generated_at }}</title>
<h1>Retrieval Metrics</h1>
<table>…precision@K, recall@K, MRR, MAP…</table>
<img src="data:image/png;base64,{{ precision_vs_k_png_b64 }}">
<h1>Response Quality</h1>
<table>…BLEU, ROUGE-1/2/L…</table>
<img src="data:image/png;base64,{{ score_histogram_png_b64 }}">
<h1>Benchmarks</h1>
<table>…p50/p95/p99/qps per stage…</table>
<img src="data:image/png;base64,{{ latency_histogram_png_b64 }}">
<h1>Baseline Comparison</h1>
<table>…deltas with regression flags…</table>
```

---

## R8: Conversation Context Retrieval — Indexed Repository Query

**Decision**: Store `ConversationTurn` rows with a compound index on `(conversation_id, turn_number DESC)`. `ConversationRepository.get_recent_turns(conversation_id, limit=N)` issues `SELECT … WHERE conversation_id = :cid ORDER BY turn_number DESC LIMIT :n` and reverses the result in Python to present chronological order to the pipeline.

**Rationale**: FR-011 caps active context at 100 turns. With an index on `(conversation_id, turn_number)` the query is an index seek + bounded scan — O(log n + k) regardless of total row count. Reversing in Python is O(k) on ≤100 rows. This preserves turn order without a full table scan even when the table holds millions of turns across all conversations.

**Alternatives considered**:
- **Load all turns, sort in Python**: O(n) per conversation — fine at 10 turns, broken at 1M.
- **LIMIT with ASC**: Would return the oldest turns, not the most recent.
- **Separate "active context" table**: Denormalization without benefit; adds write amplification.

**Sliding window semantics**: If a conversation has >100 turns, `get_recent_turns(limit=100)` returns the 100 newest. Older turns remain in the table for audit but are never loaded into active context. This matches the spec's edge case "conversation exceeds the configured maximum turn limit".

---

## R9: Health Endpoint — Cheap-Probe Strategy

**Decision**: The `/health` endpoint reports dependency status from cached in-process state, not by issuing synthetic traffic:

- **Vector store**: read `RetrieverService.is_loaded` (boolean set once at lifespan startup)
- **LLM provider**: read `GenerationPipeline.last_successful_generation_ts` (updated by the pipeline on every successful generate). "Reachable" if `now - ts < llm_health_window_seconds` (default 120s); "unreachable" otherwise
- **Database**: execute `SELECT 1` through the async engine — this is microseconds on SQLite, low-ms on MySQL
- **Uptime**: `time.time() - app.state.startup_ts`

**Rationale**: SC-003 requires `/health` to return in <1s. Synthetic LLM probes would add hundreds of ms per check, be expensive, and risk the probe itself being rate-limited. The cached-timestamp approach trades probe freshness for latency and cost — the window is configurable. It also correctly reflects a real LLM outage: if no successful calls have happened recently, the health state degrades automatically.

**Alternatives considered**:
- **Synthetic LLM call on every probe**: Slow, expensive, brittle under rate limits.
- **No LLM probe**: Violates Article VII ("Health check endpoint MUST report status of all critical dependencies").
- **Async background probe task**: More moving parts; the cached-timestamp approach achieves the same signal without a background loop.

**Trade-off disclosure**: During low-traffic periods the LLM will appear "unreachable" even when healthy. The `/health` response distinguishes "degraded" from "failed" so orchestrators can choose whether to drain traffic. For production, operators can add a periodic keep-alive task in a later feature.

---

## R10: Baseline Metric Comparison & Regression Threshold

**Decision**: Store the baseline as a JSON file at `data/evaluation/baseline_metrics.json`, committed to the repo. Each new evaluation run loads this file and compares every metric against its baseline value. A regression is flagged when `(baseline - current) / baseline > eval_regression_threshold` (default 0.05, i.e. 5% relative drop). The report lists deltas with clear "PASS" / "REGRESS" indicators and a summary verdict.

**Rationale**: FR-020 requires flagging regressions. A committed baseline file makes regression detection reproducible across machines and CI runs. Relative threshold (5% drop) is robust across metric scales — a 0.01 absolute drop means different things for precision (often ~0.3) vs. ROUGE-L (often ~0.5). The threshold is configurable via `Settings.eval_regression_threshold` so operators can tighten it as the system stabilizes.

**Alternatives considered**:
- **Absolute threshold (e.g., drop > 0.02)**: Too lenient on high-scoring metrics, too strict on low-scoring ones.
- **Standard deviation band**: Requires historical runs; we don't have them in Phase 3.
- **No baseline, just report current**: Violates FR-020.
- **Per-metric custom thresholds**: Over-engineered; start with one global threshold, split only when data demands it.

**Baseline file shape**:

```json
{
  "generated_at": "2026-04-09T12:00:00Z",
  "mrag_version": "0.1.0",
  "retrieval": {
    "precision_at_1": 0.62, "precision_at_5": 0.41,
    "recall_at_10": 0.78, "mrr": 0.55, "map": 0.48
  },
  "response": { "bleu": 0.32, "rouge_1": 0.51, "rouge_2": 0.28, "rouge_l": 0.47 },
  "benchmark": { "p50_ms": 1200, "p95_ms": 2800, "p99_ms": 3400, "qps": 0.83 }
}
```

**Bootstrapping**: The first evaluation run after merge will produce a report and commit the result as the initial baseline. Subsequent runs compare against this file.

---

## Summary

All ten unknowns are resolved. Key library additions: `aiosqlite`, `sacrebleu`, `rouge-score`, `matplotlib`. Key architectural choices: lifespan-based resource loading, `safe_persist` wrapper for FR-012 isolation, custom retrieval metrics validated against sklearn oracles, cached-timestamp health probes, committed JSON baseline for regression detection. No unresolved `NEEDS CLARIFICATION` markers remain — ready for Phase 1 design.
