# Feature Specification: Phase 3 RAG Bonus — API Surface, Persistence & Evaluation Framework

**Feature Branch**: `004-phase3-rag-bonus`
**Created**: 2026-04-09
**Status**: Draft
**Input**: User description: "Build Phase 3 bonus (007 FastAPI Integration, 008 Database Integration, 009 Evaluation Framework) in the mrag-project-plan.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Production-Ready Question Answering API (Priority: P1)

As an API consumer (downstream application or integration partner), I want to submit a question over HTTP and receive a structured, grounded answer so that I can embed the RAG system into my own product without owning the pipeline internals.

**Why this priority**: The API is the primary external contract of the platform. Without it, no external system — dashboard, chatbot, evaluation harness, or analyst tool — can consume the RAG capability built in Phases 1 and 2. It is the single gating capability that converts internal work into deliverable product value.

**Independent Test**: Start the service, send a valid question payload to the answer endpoint, and verify the response contains the generated answer, a confidence score, the source passages cited, and per-stage timing. Then send a malformed payload and verify a structured validation error is returned without crashing the service.

**Acceptance Scenarios**:

1. **Given** the service is running with the index loaded, **When** a consumer submits a well-formed question payload to the answer endpoint, **Then** the response contains `answer`, `confidence_score`, `sources` (list of cited passages with identifiers and excerpts), and `response_time_ms`
2. **Given** a consumer submits an empty or malformed payload, **When** the request is received, **Then** the service returns a validation error with HTTP status 422 and a machine-readable error body describing the offending fields
3. **Given** the downstream language model provider is unreachable, **When** a question is submitted, **Then** the service returns a graceful fallback response with a low confidence score and an error indicator rather than crashing or hanging indefinitely
4. **Given** a consumer requests interactive documentation, **When** they open the documentation endpoint, **Then** they see an up-to-date schema for every request, response, and error with example payloads

---

### User Story 2 - Service Health & Readiness Visibility (Priority: P1)

As a system operator (on-call engineer or platform team), I want a health endpoint that reports the status of every critical dependency so that I can detect and diagnose outages before users do.

**Why this priority**: A service without health visibility cannot be safely operated. Health reporting is the minimum operational surface that lets orchestrators, load balancers, and humans make go/no-go decisions. It is P1 because it must land with the first public endpoint.

**Independent Test**: Query the health endpoint with the service fully up and verify each dependency is reported as reachable with its uptime. Then simulate a degraded dependency (e.g., unreachable language model) and verify the health endpoint reflects the degraded state without taking the whole service down.

**Acceptance Scenarios**:

1. **Given** the service is fully initialized, **When** the health endpoint is queried, **Then** it reports the status of the vector index (loaded / not_loaded), the language model provider (reachable / unreachable), the persistence store (connected / disconnected), and a process uptime in seconds
2. **Given** one dependency is degraded, **When** the health endpoint is queried, **Then** the response marks that dependency as unhealthy while still returning within one second and without raising an error
3. **Given** the service is still initializing (index not yet loaded), **When** the health endpoint is queried, **Then** the response reports a "not ready" state so that orchestrators can delay traffic routing

---

### User Story 3 - Query History Persistence for Analytics & Audit (Priority: P1)

As a system operator, I want every question and answer the service handles to be persisted so that I can audit usage, investigate incidents, and analyse patterns over time.

**Why this priority**: Without persistence, the system is ephemeral — no incident investigation, no compliance trail, no usage analytics. It is P1 because Features 007 and 008 must land together for any production deployment, and downstream analytics in later stories depend on the data being captured from day one.

**Independent Test**: Submit a question through the API, then query the persistence store and verify a record exists with the question text, generated answer, confidence score, per-stage latency breakdown, cache-hit indicator, and a timestamp. Submit a second question and verify a second distinct record is created.

**Acceptance Scenarios**:

1. **Given** a question is processed end-to-end, **When** the response is returned to the caller, **Then** a persisted record exists containing the question text, answer text, confidence score, embedding / search / generation / total latency, cache-hit flag, and creation timestamp
2. **Given** persistence is temporarily unavailable, **When** a question is processed, **Then** the service still returns a valid answer to the caller and logs the persistence failure without losing the in-memory result
3. **Given** thousands of queries have been persisted, **When** an operator queries by time range, **Then** records are returned in chronological order without requiring a full table scan

---

### User Story 4 - Retrieval Quality Evaluation (Priority: P1)

As a platform developer, I want automated measurement of retrieval quality against a held-out dataset so that I can prove the system meets accuracy targets and detect regressions before they reach users.

**Why this priority**: The constitution mandates that retrieval quality is validated with metrics before merging — without this capability, no retrieval change can be safely shipped. It is P1 because it is the regression gate for every subsequent retrieval or ranking change across the project.

**Independent Test**: Run the evaluation suite on a held-out set of questions with known relevant passages and verify precision@K, recall@K, mean reciprocal rank, and mean average precision are computed for K values of 1, 3, 5, and 10. Verify the numbers match a hand-computed baseline on a small fixture.

**Acceptance Scenarios**:

1. **Given** a held-out evaluation dataset with known-relevant passages per query, **When** the retrieval evaluation runs, **Then** precision@K, recall@K, mean reciprocal rank (MRR), and mean average precision (MAP) are reported for K = 1, 3, 5, 10
2. **Given** a known-answer fixture where the expected metric values are pre-computed, **When** the evaluator runs on that fixture, **Then** the returned metric values match the expected values within numerical tolerance
3. **Given** a baseline metric file from a previous run, **When** the evaluator compares new metrics to baseline, **Then** regressions above a configured threshold are flagged

---

### User Story 5 - Response Quality Evaluation (Priority: P2)

As a platform developer, I want automated measurement of generated answer quality against reference answers so that I can quantify how closely the system matches expected responses and track quality trends.

**Why this priority**: Response quality metrics (text overlap scores) measure the LLM-facing half of the pipeline. They are P2 because retrieval quality (Story 4) is the stronger leading indicator of overall system health, but response quality is still required to complete the evaluation story and is explicitly mandated by the constitution.

**Independent Test**: Provide a small set of (generated_answer, reference_answer) pairs with known scores. Run response evaluation and verify the computed overlap scores fall within expected bounds: identical strings score 1.0, disjoint strings score 0.0, and partial overlaps score between them monotonically.

**Acceptance Scenarios**:

1. **Given** a set of generated answers and their ground-truth reference answers, **When** response quality evaluation runs, **Then** n-gram overlap metrics (BLEU) and longest-common-subsequence metrics (ROUGE-1, ROUGE-2, ROUGE-L) are reported for each pair and in aggregate
2. **Given** an answer that exactly matches its reference, **When** evaluated, **Then** all overlap scores are at their maximum value
3. **Given** an answer with no shared tokens with its reference, **When** evaluated, **Then** all overlap scores are zero

---

### User Story 6 - Performance Benchmarking & Reporting (Priority: P2)

As a system operator, I want a repeatable latency and throughput benchmark so that I can track performance over time and present results to stakeholders in a human-readable report.

**Why this priority**: Benchmarks and visual reports are essential for stakeholder communication and for validating the constitution's latency targets (p50/p95/p99). They are P2 because they enhance visibility rather than enable functionality — the system is usable without them, but unmeasurable.

**Independent Test**: Run the benchmark on a fixed workload of 100 queries. Verify the output contains p50, p95, and p99 latency per stage plus overall throughput. Generate the report and verify an output artifact is produced containing the metrics and charts.

**Acceptance Scenarios**:

1. **Given** a benchmark workload of 100 queries, **When** the benchmark runs, **Then** p50, p95, p99 latency and queries-per-second throughput are computed and returned
2. **Given** a completed evaluation run, **When** the report generator runs, **Then** a human-readable report file is produced containing retrieval metrics, response quality metrics, latency distributions, and comparison charts
3. **Given** a prior baseline report exists, **When** a new report is generated, **Then** the report includes a delta view highlighting metric changes against the baseline

---

### User Story 7 - Conversation Context Tracking (Priority: P2)

As an end user of a downstream chat application, I want my follow-up questions to be understood in the context of prior turns so that I don't have to re-state what I'm asking about every time.

**Why this priority**: Multi-turn conversation improves usability substantially but is not required for single-shot question answering. It is P2 because it layers on top of the Story 1 answer endpoint and requires persistence from Story 3, making it the natural follow-on capability rather than a launch-blocking one.

**Independent Test**: Submit a question with a conversation identifier, then submit a follow-up referencing "it" with the same identifier. Verify the second response resolves the reference correctly by retrieving the same subject as the first question.

**Acceptance Scenarios**:

1. **Given** a new conversation identifier, **When** a consumer sends a question, **Then** a conversation turn is persisted linking the question, answer, and turn number to that identifier
2. **Given** an existing conversation with prior turns, **When** a follow-up question is submitted with the same identifier, **Then** prior turns are retrieved and used as context for answering the follow-up
3. **Given** a conversation exceeds the configured maximum turn limit, **When** a new turn is submitted, **Then** the oldest turns are dropped from the active context window while remaining persisted for audit

---

### User Story 8 - Usage Analytics & Reporting (Priority: P3)

As a system operator, I want aggregated usage analytics so that I can produce reports on how the system is being used, which topics are popular, and how performance trends over time.

**Why this priority**: Analytics are valuable for product decisions and capacity planning but are not required for the system to function. They sit at P3 because they are purely observational, downstream of persistence, and consumed by humans on their own schedule.

**Independent Test**: Process twenty distinct questions through the API, then request analytics and verify the response includes total query count, average latency, cache hit rate, top domains or topics, and queries per day.

**Acceptance Scenarios**:

1. **Given** a history of persisted queries, **When** an operator requests analytics, **Then** the response includes `total_queries`, `avg_latency_ms`, `cache_hit_rate`, `top_domains`, and `queries_per_day`
2. **Given** analytics data for a specific time window, **When** a windowed query is submitted, **Then** only records within that window contribute to the aggregated metrics
3. **Given** the persistence store holds up to one hundred thousand query records, **When** analytics are requested, **Then** the response is produced in under one second

---

### Edge Cases

- What happens when the language model provider is unreachable during an API request? The service returns a structured fallback response with a low confidence score; the request is still persisted with an error indicator so the incident is auditable.
- What happens when persistence is temporarily unavailable? The API continues serving responses; persistence errors are logged and the in-memory result is still returned to the caller.
- What happens when the vector index has not finished loading at startup? The answer endpoint returns a "service initializing" status and the health endpoint reports the index as not_loaded until ready.
- What happens when an evaluation dataset contains queries for which no ground-truth relevant passages exist? Those queries are excluded from precision/recall computation but counted separately in the report.
- What happens when response quality evaluation receives empty predicted or reference text? Scores default to zero and the empty case is flagged in the report.
- What happens when a conversation identifier is reused after its turns have been archived? A new active context window is started; archived turns remain retrievable for audit but are not automatically reloaded.
- What happens when analytics are requested before any queries have been persisted? The response returns zero-valued metrics instead of raising an error.
- What happens when a caller submits a question in a non-English language? The existing multilingual pipeline handles it end-to-end; the API does not restrict language.

## Requirements *(mandatory)*

### Functional Requirements

#### API Surface (Feature 007)

- **FR-001**: System MUST expose an HTTP endpoint that accepts a question payload and returns a structured response containing the generated answer, a confidence score, the list of cited source passages, and per-stage timing
- **FR-002**: System MUST validate every incoming request against a published schema and reject malformed requests with a structured validation error and an HTTP 422 status
- **FR-003**: System MUST expose an HTTP health endpoint that reports the readiness of the vector index, the language model provider, the persistence store, and the process uptime in seconds
- **FR-004**: System MUST expose an HTTP endpoint that triggers an evaluation run and returns the resulting metrics
- **FR-005**: System MUST publish interactive API documentation describing every endpoint, schema, status code, and example payload
- **FR-006**: System MUST return a consistent error response shape containing an error code, a human-readable detail, and an HTTP status code for every failure mode
- **FR-007**: System MUST configure cross-origin resource sharing so that approved consumer origins can call the API from browser contexts
- **FR-008**: System MUST load the vector index and generation models at service startup and fail fast if required resources are missing, so that degraded state is detectable at boot

#### Persistence (Feature 008)

- **FR-009**: System MUST persist every question-answer exchange with question text, answer text, confidence score, per-stage latencies, cache-hit indicator, and creation timestamp
- **FR-010**: System MUST associate persisted exchanges with an optional conversation identifier and assign a monotonically increasing turn number per conversation
- **FR-011**: System MUST retrieve prior conversation turns by conversation identifier for use as context in follow-up questions, up to a configurable maximum of one hundred turns
- **FR-012**: System MUST continue to serve API responses when persistence is temporarily unavailable; persistence failures MUST be logged and MUST NOT block the caller
- **FR-013**: System MUST support aggregated analytics queries returning total query count, average latency, cache hit rate, top domains or topics, and queries per day
- **FR-014**: System MUST resolve persistence connection details from environment configuration so that credentials are never committed to source control
- **FR-015**: System MUST support both a lightweight embedded persistence store for local development and a server-based persistence store for production via the same code path

#### Evaluation Framework (Feature 009)

- **FR-016**: System MUST compute retrieval quality metrics — precision@K, recall@K, mean reciprocal rank, and mean average precision — for K values of 1, 3, 5, and 10 against a held-out dataset
- **FR-017**: System MUST compute response quality metrics — n-gram overlap (BLEU) and longest-common-subsequence overlap (ROUGE-1, ROUGE-2, ROUGE-L) — for generated answers against reference answers
- **FR-018**: System MUST produce latency benchmarks reporting p50, p95, and p99 per pipeline stage and overall, plus queries-per-second throughput, over a configurable workload size
- **FR-019**: System MUST generate a human-readable report artifact containing all evaluation metrics with embedded charts for precision-vs-K, latency distribution, and score histograms
- **FR-020**: System MUST compare new evaluation runs against a prior baseline and flag any metric regression exceeding a configured threshold
- **FR-021**: System MUST validate its metric implementations against a known-answer fixture so that metric correctness can be proven by test, not only asserted
- **FR-022**: System MUST allow the evaluation runner to be invoked both from the API endpoint and as a standalone process, so that batch evaluation is possible without starting the full service

### Key Entities

- **QuestionRequest**: An incoming consumer request containing the question text and optional conversation identifier; validated at the API boundary
- **QuestionResponse**: The outbound payload containing the generated answer, confidence score, source citations with identifiers and excerpts, and per-stage timing
- **HealthReport**: A snapshot of dependency readiness (vector index, language model, persistence store) and process uptime
- **ErrorEnvelope**: A consistent error shape with error code, detail, and HTTP status used for every failure response
- **QueryRecord**: A persisted record of a single question-answer exchange including text, scores, latency breakdown, cache hit, conversation reference, and timestamp
- **ConversationTurn**: A turn within a conversation, linking question and answer to a conversation identifier and turn number for context reconstruction
- **AnalyticsSnapshot**: An aggregated view over a time window containing total queries, average latency, cache hit rate, top topics, and daily counts
- **EvaluationDataset**: A held-out set of questions, each optionally paired with relevant passage identifiers and reference answers, used as ground truth for metric computation
- **RetrievalMetrics**: Computed precision@K, recall@K, MRR, and MAP for a given dataset and K range
- **ResponseQualityMetrics**: Computed BLEU and ROUGE scores for a set of (generated, reference) answer pairs
- **BenchmarkResult**: p50/p95/p99 latency and throughput for a benchmark workload
- **EvaluationReport**: The aggregated artifact combining retrieval metrics, response quality metrics, benchmark results, and baseline comparison, rendered as a human-readable report

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A downstream consumer can submit a well-formed question to the API and receive a grounded answer with citations within three seconds at the 95th percentile end-to-end
- **SC-002**: Every malformed API request is rejected with a structured validation error that identifies the offending field, and no malformed request ever crashes the service
- **SC-003**: The health endpoint returns within one second and accurately reflects the state of every critical dependency, including during simulated dependency outages
- **SC-004**: 100% of question-answer exchanges handled by the API are persisted for audit, with persistence adding less than 50 milliseconds to the end-to-end response time
- **SC-005**: Analytics queries over up to one hundred thousand persisted records return in under one second
- **SC-006**: Conversation context retrieval supports up to one hundred turns per conversation and correctly preserves turn order
- **SC-007**: The evaluation suite runs end-to-end on a held-out dataset and reports precision@K, recall@K, MRR, MAP, BLEU, and ROUGE scores that match a hand-computed baseline on a small fixture within numerical tolerance
- **SC-008**: Latency benchmarks produce stable p50, p95, and p99 measurements across repeated runs with less than 10% variance on identical workloads
- **SC-009**: An evaluation report artifact is produced as a single human-readable file containing all metrics and at least three charts (precision-vs-K, latency distribution, score histogram)
- **SC-010**: When a new evaluation run shows a metric regression above the configured threshold compared to the baseline, the regression is clearly flagged in the report
- **SC-011**: A persistence outage does not cause any API request to fail; failed persistence writes are logged and surfaced for operator review
- **SC-012**: API endpoints, persistence, and the evaluation runner all run correctly on Apple Silicon without any GPU dependency

## Assumptions

- Phase 1 (data processing, embedding, vector store, basic retrieval) and Phase 2 (query processing, response generation, caching, performance metrics) are complete and their modules are importable and usable as libraries
- The Groq-compatible language model API is reachable from the deployment environment via an API key stored in environment variables
- The conda environment `mrag` is the target execution environment for both the API service and the evaluation runner
- The deployment target is Apple Silicon; all computation runs on CPU via the existing Phase 1/2 pipeline with no CUDA or NVIDIA dependency
- A lightweight embedded persistence store is acceptable for local development; production will use a server-based store, both reached via the same abstraction
- Database credentials and API keys are supplied via environment variables or a gitignored `.env` file, consistent with existing project configuration discipline
- Conversation context is treated as a sliding window of recent turns; older turns remain persisted for audit but are not automatically loaded into context
- The held-out evaluation dataset is a labelled subset of the project's Natural Questions source data, or a compatible external dataset with the same schema
- Reference implementations from standard libraries (e.g., scikit-learn for precision/recall) are the source of truth for metric correctness validation
- Report artifacts are produced as self-contained files (HTML or similar) that can be opened without a running service
- The API service and the evaluation runner share the same retrieval and generation components, so a regression in one is observable from the other
- Operator access to analytics and evaluation endpoints is assumed to be behind a trusted network boundary in this phase; richer authentication and authorisation are out of scope for Phase 3
