# Quickstart: Phase 2 RAG Pipeline

## Prerequisites

- Phase 1 complete: FAISS index built, metadata store populated
- conda environment `mrag` activated
- `.env` file with `LLM_API_KEY` set (Groq API key)

## Setup

```bash
# Activate environment
conda activate mrag

# Install updated dependencies (adds Jinja2)
pip install -e ".[dev]"

# Verify Phase 1 artifacts exist
ls data/processed/*.faiss data/processed/*_metadata.json
```

## Configuration

Key `.env` settings for Phase 2:

```bash
# Required
LLM_API_KEY=gsk_your_groq_api_key_here

# Optional (defaults shown)
LLM_API_URL=https://api.groq.com/openai/v1
LLM_MODEL_NAME=llama3-8b-8192
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1024
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=3
CONFIDENCE_THRESHOLD=0.3
QUERY_EXPANSION_ENABLED=true
QUERY_EXPANSION_TOP_N=3
CONVERSATION_HISTORY_MAX_TURNS=5
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
```

## Quick Verification

```python
from mrag.query.preprocessor import QueryPreprocessor
from mrag.query.pipeline import QueryPipeline
from mrag.generation.llm_client import GroqLLMClient
from mrag.generation.pipeline import GenerationPipeline
from mrag.cache.metrics import MetricsCollector
from mrag.config import get_settings

settings = get_settings()

# Test query preprocessing
preprocessor = QueryPreprocessor()
result = preprocessor.normalize("  What  IS   Photosynthesis?? ")
assert result == "what is photosynthesis?"

# Test LLM connectivity (async)
import asyncio
client = GroqLLMClient(
    api_url=settings.llm_api_url,
    api_key=settings.llm_api_key.get_secret_value(),
)
response = asyncio.run(client.generate("Say hello in one word."))
print(response)
```

## Running Tests

```bash
# Unit tests only (no LLM API needed)
pytest tests/unit/test_preprocessor.py tests/unit/test_context_manager.py tests/unit/test_embedding_cache.py tests/unit/test_response_cache.py tests/unit/test_metrics.py -v

# Integration tests (requires LLM_API_KEY and Phase 1 index)
pytest tests/integration/test_phase2_e2e.py -v

# All tests
make test
```

## Module Usage

### Query Processing

```python
from mrag.query.pipeline import QueryPipeline
from mrag.query.preprocessor import QueryPreprocessor
from mrag.query.expander import QueryExpander
from mrag.query.context_manager import ConversationContextManager

pipeline = QueryPipeline(
    preprocessor=QueryPreprocessor(),
    expander=QueryExpander(retriever=retriever, encoder=encoder),
    context_manager=ConversationContextManager(max_turns=5),
)

processed = pipeline.process("What is DNA?")
```

### Response Generation

```python
from mrag.generation.pipeline import GenerationPipeline
from mrag.generation.llm_client import GroqLLMClient
from mrag.generation.prompt_builder import PromptBuilder
from mrag.generation.validator import ResponseValidator
from mrag.generation.fallback import FallbackHandler

gen_pipeline = GenerationPipeline(
    llm_client=GroqLLMClient(...),
    prompt_builder=PromptBuilder(),
    validator=ResponseValidator(confidence_threshold=0.3),
    fallback_handler=FallbackHandler(),
)

response = await gen_pipeline.generate_answer(
    query="What is photosynthesis?",
    retrieval_results=results,
)
```

### Caching & Metrics

```python
from mrag.cache.embedding_cache import EmbeddingCache
from mrag.cache.response_cache import ResponseCache
from mrag.cache.metrics import MetricsCollector

emb_cache = EmbeddingCache(max_size=1000)
resp_cache = ResponseCache(max_size=1000, default_ttl=3600)
metrics = MetricsCollector()

# Metrics summary after processing queries
summary = metrics.get_summary()
print(summary["total_time_ms"]["p95"])
```
