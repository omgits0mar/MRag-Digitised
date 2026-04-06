# Project Constitution

**Project Name:** Multilingual RAG Platform (MRAG)
**Version:** 1.0.0
**Ratification Date:** 2026-04-02
**Last Amended:** 2026-04-02

---

## Preamble

This constitution establishes the non-negotiable principles, governance rules, and development standards for the **Multilingual RAG Platform** — an AI-powered Retrieval-Augmented Generation system that handles diverse knowledge domains with efficient semantic search, multilingual processing, and scalable architecture. Every specification, plan, task, and line of code produced for this project **MUST** comply with the articles defined herein. The constitution supersedes all other practices and assumptions.

---

## Article I — Modular Architecture (NON-NEGOTIABLE)

Every component of this system MUST be designed as an independent, self-contained module with explicit input/output contracts. No feature shall be implemented as a monolithic block.

The system is decomposed into the following core modules, each with clear boundaries:

- **Data Processing Module:** Dataset acquisition, text chunking, metadata enrichment, and answer extraction.
- **Embedding Module:** Multilingual embedding generation using Sentence Transformers.
- **Vector Store Module:** FAISS-based indexing, similarity search, and metadata-aware retrieval.
- **Query Processing Module:** Query preprocessing, normalization, expansion, and multi-turn context management.
- **Response Generation Module:** LLM API integration, prompt engineering, quality filtering, and fallback handling.
- **Caching & Performance Module:** Intelligent caching, batch processing, and metrics collection.
- **API Module (Bonus):** FastAPI endpoints, request validation, and error handling.
- **Evaluation Module (Bonus):** Retrieval accuracy, response quality metrics, and benchmarking.
- **Database Module (Bonus):** SQLAlchemy models, conversation tracking, and analytics persistence.

**Rationale:** Modular design enables independent testing, replacement of components (e.g., swapping FAISS for another vector store), and parallel development across phases.

---

## Article II — Data Integrity & Preprocessing Discipline (NON-NEGOTIABLE)

All data entering the system MUST pass through a validated preprocessing pipeline. Raw data is never consumed directly by downstream components.

- The Natural Questions dataset (or equivalent) MUST be fully preprocessed before any embedding or indexing operation.
- Text chunking strategies MUST be configurable (chunk size, overlap) and benchmarked for retrieval quality.
- Metadata enrichment (question types, domains, difficulty levels) MUST be systematic, reproducible, and documented.
- Short-form and long-form answers MUST be handled with distinct processing paths — they are not interchangeable.
- All preprocessing steps MUST be logged and reproducible from raw source to final indexed documents.
- Data validation checks MUST exist at every pipeline boundary (ingestion → chunking → enrichment → embedding → indexing).

**Rationale:** Garbage in, garbage out. The quality of a RAG system is bounded by the quality of its data pipeline. Skipping validation leads to silent retrieval failures that are nearly impossible to debug in production.

---

## Article III — Multilingual-First Design (NON-NEGOTIABLE)

The system MUST treat multilingual support as a first-class architectural concern, not a bolt-on feature.

- Embedding models MUST be multilingual-capable from the outset (e.g., `paraphrase-multilingual-MiniLM-L12-v2` or equivalent Sentence Transformer models).
- Text processing pipelines MUST handle Unicode properly — no ASCII-only assumptions in tokenization, normalization, or chunking.
- Query processing MUST normalize input across scripts and languages before embedding.
- All string operations MUST be encoding-safe (UTF-8 throughout).
- Language detection SHOULD be implemented to route queries through appropriate processing paths when applicable.

**Rationale:** Retrofitting multilingual support is exponentially harder than designing for it. The project requirements explicitly mandate multilingual RAG capabilities.

---

## Article IV — Retrieval Quality Over Speed (NON-NEGOTIABLE)

When retrieval accuracy and retrieval speed conflict, accuracy wins. Performance optimizations MUST NOT degrade retrieval quality without explicit, documented justification and measurable trade-off analysis.

- Top-K retrieval MUST be configurable and default to a sensible value (K=5) with the ability to adjust per query.
- Relevance scoring and ranking algorithms MUST be implemented and benchmarked — raw cosine similarity alone is insufficient for production.
- Query expansion techniques MUST be evaluated against baseline retrieval before being enabled by default.
- All retrieval changes MUST be validated against precision@K and recall@K metrics before merging.
- FAISS index type selection (Flat, IVF, HNSW) MUST be justified by the dataset size and accuracy requirements, not assumed.

**Rationale:** A fast system that returns wrong answers is worse than useless. Users trust RAG systems to provide grounded, relevant responses.

---

## Article V — LLM Integration as a Replaceable Contract (NON-NEGOTIABLE)

The LLM integration layer MUST be designed as an abstraction with a clear interface contract. The system MUST NOT be coupled to any single LLM provider.

- LLM calls MUST go through a unified interface (e.g., `BaseLLMClient`) that abstracts provider-specific details.
- Prompt templates MUST be externalized and version-controlled — never hardcoded in business logic.
- Context-aware prompt engineering MUST inject retrieved documents, conversation history, and system instructions through a structured prompt builder.
- Response quality filtering MUST validate LLM output before returning to the user (hallucination checks, confidence scoring).
- Fallback mechanisms MUST exist for low-confidence answers — the system should say "I don't know" rather than hallucinate.
- API keys and provider configuration MUST be environment-variable driven, never committed to source control.

**Rationale:** LLM providers evolve rapidly. Tight coupling to Groq or any single provider creates vendor lock-in and makes the system fragile to API changes or deprecations.

---

## Article VI — Testing & Evaluation as First-Class Citizens (NON-NEGOTIABLE)

Every module MUST have tests. The evaluation framework is not optional "bonus" work — it is the mechanism by which we know the system actually works.

- **Unit Tests:** Every module MUST have unit tests covering core logic (chunking, embedding, retrieval, ranking).
- **Integration Tests:** The full pipeline (query → retrieval → generation → response) MUST have end-to-end tests.
- **Retrieval Evaluation:** Precision@K, Recall@K, and MRR (Mean Reciprocal Rank) MUST be computed on a held-out evaluation set.
- **Response Quality Evaluation:** BLEU and ROUGE scores MUST be computed where ground-truth answers are available.
- **Performance Benchmarks:** Latency (p50, p95, p99) and throughput (queries/second) MUST be measured and tracked.
- **Regression Testing:** Any change to embedding models, chunking strategies, or ranking algorithms MUST be validated against the evaluation suite before deployment.
- Test data MUST be version-controlled and reproducible.

**Rationale:** The project requirements explicitly include an evaluation framework. More importantly, RAG systems degrade silently — without quantitative evaluation, you cannot detect drift or regression.

---

## Article VII — API Design & Error Handling Standards (NON-NEGOTIABLE)

All API endpoints MUST follow consistent design patterns with proper validation, error handling, and documentation.

- FastAPI MUST be used with async support for all I/O-bound operations (LLM calls, database queries, embedding generation).
- Request/response models MUST use Pydantic for validation — no raw dictionary passing at API boundaries.
- Error responses MUST follow a consistent schema: `{"error": str, "detail": str, "status_code": int}`.
- All endpoints MUST have OpenAPI documentation with examples.
- Health check endpoint (`GET /health`) MUST report status of all critical dependencies (vector store, LLM provider, database).
- Rate limiting and input validation MUST prevent abuse and injection attacks on the query endpoint.
- CORS, authentication, and security headers MUST be configured appropriately for the deployment context.

**Rationale:** The API is the system's contract with the outside world. Poor API design makes the system unusable regardless of how good the underlying RAG pipeline is.

---

## Article VIII — Performance & Caching Discipline (NON-NEGOTIABLE)

Performance optimization MUST be data-driven, not speculative. Caching MUST be implemented with explicit invalidation strategies.

- Embedding caching MUST be implemented for repeated or similar queries to avoid redundant model inference.
- Search result caching MUST use an LRU or TTL-based strategy with configurable expiration.
- Batch processing MUST be supported for bulk query evaluation and dataset re-indexing.
- Performance metrics (embedding time, search time, LLM response time, total latency) MUST be collected on every request.
- Optimization decisions MUST be backed by profiling data — no premature optimization.
- Memory usage of FAISS indices MUST be monitored and documented, especially for large datasets.

**Rationale:** Caching without invalidation is a bug factory. Performance without measurement is guesswork. The project requirements explicitly call for performance optimization and metrics collection.

---

## Article IX — Code Quality & Development Standards (NON-NEGOTIABLE)

All code MUST meet minimum quality standards regardless of development speed pressures.

- **Language:** Python 3.10+ with type hints on all function signatures.
- **Formatting:** Code MUST pass `black` formatting and `ruff` or `flake8` linting with zero violations.
- **Documentation:** Every public function and class MUST have a docstring describing purpose, parameters, return values, and exceptions.
- **Configuration:** All configurable values (model names, chunk sizes, top-K, API URLs) MUST be externalized to configuration files or environment variables — no magic numbers in source code.
- **Logging:** Structured logging MUST be used throughout (not print statements). Log levels MUST be appropriate (DEBUG for development detail, INFO for operational events, WARNING for recoverable issues, ERROR for failures).
- **Dependency Management:** Dependencies MUST be pinned in `requirements.txt` or `pyproject.toml` with exact versions for reproducibility.
- **Git Hygiene:** Commits MUST be atomic and descriptive. Each completed task gets its own commit. Force-pushing to shared branches is prohibited.
- **Secrets Management:** API keys, database credentials, and sensitive configuration MUST use environment variables or `.env` files (which are `.gitignore`d). Never committed to version control.

**Rationale:** These are baseline professional standards. Cutting corners here creates compounding technical debt that slows every subsequent phase.

---

## Article X — Documentation Separation of Concerns (NON-NEGOTIABLE)

Documentation follows strict separation between WHAT/WHY (specifications) and HOW (plans and implementation).

- **Specifications (spec.md):** MUST remain technology-agnostic. Focus on user stories, requirements, success criteria, and business value. No framework names, no implementation details.
- **Plans (plan.md):** Contain ALL technical decisions — architecture patterns, library choices, data flow diagrams, API contracts. This is where FastAPI, FAISS, Sentence Transformers, and SQLAlchemy are discussed.
- **Tasks (tasks.md):** Atomic, actionable work items derived from the plan. Each task has a clear definition of done.
- **Constitution (this document):** Immutable principles that govern all other documents. Never contains implementation-level detail.

**Rationale:** When specifications mix "what" with "how," changing the tech stack means rewriting requirements. Clean separation allows the same spec to generate multiple plans for different technology choices.

---

## Phase Structure & Development Roadmap

The project is executed in three sequential phases. Each phase MUST be fully validated (tests passing, evaluation metrics collected) before proceeding to the next.

### Phase 1: Dataset Processing & RAG Foundation
**Scope:** Data pipeline, multilingual embeddings, FAISS vector store, basic retrieval.
**Exit Criteria:** Preprocessed dataset indexed in FAISS. Basic query → retrieval pipeline functional. Retrieval metrics (precision@K, recall@K) established as baseline.

### Phase 2: Advanced RAG Features
**Scope:** Query enhancement, LLM-powered response generation, caching, performance optimization.
**Exit Criteria:** End-to-end query → retrieval → generation pipeline functional. Caching operational. Performance metrics collected. Fallback mechanisms tested.

### Phase 3: API Development & Evaluation (Bonus)
**Scope:** FastAPI endpoints, database integration, comprehensive evaluation framework.
**Exit Criteria:** All API endpoints functional with proper error handling. Evaluation suite producing precision@K, recall@K, BLEU, ROUGE, and latency reports. Database persisting query analytics.

---

## Technology Stack Constraints

The following technology choices are mandated by the project requirements and MUST NOT be substituted without a formal amendment to this constitution:

| Component | Technology | Justification |
|---|---|---|
| Backend Framework | FastAPI (async) | Project requirement; async support for I/O-bound operations |
| Database ORM | SQLAlchemy | Project requirement; MySQL/SQLite support |
| Embeddings | Sentence Transformers (multilingual) | Project requirement; multilingual capability |
| Vector Search | FAISS | Project requirement; efficient similarity search |
| LLM Integration | API-based (Groq-compatible interface) | Project requirement; abstracted behind interface contract |
| Data Processing | Pandas, NumPy | Project requirement; dataset handling |
| Evaluation | scikit-learn metrics + custom functions | Project requirement; retrieval and response quality |

---

## Governance

### Amendment Process

Modifications to this constitution require:

1. **Written Rationale:** A clear, documented explanation of why the amendment is necessary.
2. **Impact Assessment:** Analysis of how the change affects existing specifications, plans, and tasks.
3. **Backwards Compatibility:** Amendments MUST NOT invalidate previously approved specifications unless a migration path is documented.
4. **Version Increment:** All amendments MUST update the constitution version following semantic versioning:
   - **MAJOR:** Principle removed, redefined, or fundamentally altered.
   - **MINOR:** New principle added or existing principle materially expanded.
   - **PATCH:** Clarifications, wording improvements, typo fixes.

### Compliance Review

- Every specification MUST include a "Constitution Compliance" section confirming alignment with all applicable articles.
- Every plan MUST reference the constitution version it was written against.
- Every pull request / code review MUST verify compliance with relevant articles.
- Deviations from any article MUST be documented with explicit justification and approved before merging.

### Decision Authority

- The **Project Manager** (constitution author) has final authority on principle interpretation.
- Technical decisions that conflict with constitutional principles MUST be escalated to the Project Manager.
- Complexity MUST be justified. If a simpler approach satisfies the requirements, the simpler approach wins.

---

## Amendments Log

| Version | Date | Description |
|---|---|---|
| 1.0.0 | 2026-04-02 | Initial ratification. Ten articles covering modular architecture, data integrity, multilingual design, retrieval quality, LLM abstraction, testing, API standards, performance, code quality, and documentation separation. |

---

*This constitution is the architectural DNA of the Multilingual RAG Platform. It is actively referenced before every specification, plan, and implementation decision. All team members and AI agents working on this project are bound by its principles.*