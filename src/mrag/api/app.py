"""FastAPI application factory and lifespan handler.

Loads heavy Phase 1/2 resources at startup, creates the async DB engine,
initialises the evaluation runner, and registers all routes/middleware.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mrag.api.middleware import register_middleware
from mrag.api.routes.analytics import router as analytics_router
from mrag.api.routes.ask import router as ask_router
from mrag.api.routes.evaluate import router as evaluate_router
from mrag.api.routes.health import router as health_router
from mrag.cache.embedding_cache import EmbeddingCache
from mrag.cache.metrics import MetricsCollector
from mrag.cache.response_cache import ResponseCache
from mrag.config import get_settings
from mrag.db.engine import create_db_engine, create_session_factory
from mrag.db.schema_init import create_tables
from mrag.embeddings.encoder import EmbeddingEncoder
from mrag.embeddings.indexer import FAISSIndexer
from mrag.embeddings.metadata_store import MetadataStore
from mrag.evaluation.runner import EvaluationRunner
from mrag.generation.fallback import FallbackHandler
from mrag.generation.llm_client import GroqLLMClient
from mrag.generation.pipeline import GenerationPipeline
from mrag.generation.prompt_builder import PromptBuilder
from mrag.generation.validator import ResponseValidator
from mrag.pipeline import MRAGPipeline
from mrag.query.pipeline import QueryPipeline

logger = structlog.get_logger(__name__)


async def build_mrag_pipeline() -> MRAGPipeline:
    """Construct the full Phase 2 MRAGPipeline from settings.

    Loads FAISS index, metadata store, encoder, and wires together
    all pipeline components.
    """
    settings = get_settings()

    # Encoder
    encoder = EmbeddingEncoder(model_name=settings.embedding_model_name)

    # FAISS index + metadata
    indexer = FAISSIndexer(dimension=settings.embedding_dimension)
    metadata_store = MetadataStore()

    # Load existing index artifacts from Phase 1
    import os

    index_path = os.path.join(settings.data_dir, "processed", "embeddings.faiss")
    metadata_path = os.path.join(
        settings.data_dir, "processed", "embeddings_metadata.json"
    )

    if os.path.exists(index_path):
        indexer.load(index_path)
        logger.info("faiss_index_loaded", path=index_path)
    else:
        logger.warning("faiss_index_not_found", path=index_path)

    if os.path.exists(metadata_path):
        metadata_store.load(metadata_path)
        logger.info("metadata_store_loaded", path=metadata_path)

    # Embedding cache
    embedding_cache = EmbeddingCache(
        max_size=settings.cache_max_size,
        ttl_seconds=settings.cache_ttl_seconds,
    )

    # Retriever
    from mrag.retrieval.retriever import RetrieverService

    retriever = RetrieverService(
        encoder=encoder,
        indexer=indexer,
        metadata_store=metadata_store,
        embedding_cache=embedding_cache,
    )

    # LLM client
    llm_client = GroqLLMClient(
        api_url=settings.llm_api_url,
        api_key=settings.llm_api_key.get_secret_value(),
        model_name=settings.llm_model_name,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )

    # Generation components
    prompt_builder = PromptBuilder(prompts_dir=settings.prompts_dir)
    validator = ResponseValidator(confidence_threshold=settings.confidence_threshold)
    fallback_handler = FallbackHandler()

    generation_pipeline = GenerationPipeline(
        llm_client=llm_client,
        prompt_builder=prompt_builder,
        validator=validator,
        fallback_handler=fallback_handler,
    )

    # Query pipeline
    query_pipeline = QueryPipeline(
        expansion_enabled=settings.query_expansion_enabled,
        expansion_top_n=settings.query_expansion_top_n,
    )

    # Response cache
    response_cache = ResponseCache(
        ttl_seconds=settings.cache_ttl_seconds,
        max_size=settings.cache_max_size,
    )

    # Metrics
    metrics_collector = MetricsCollector()

    return MRAGPipeline(
        query_pipeline=query_pipeline,
        retriever=retriever,
        generation_pipeline=generation_pipeline,
        embedding_cache=embedding_cache,
        response_cache=response_cache,
        metrics_collector=metrics_collector,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load heavy resources at startup; dispose at shutdown."""
    settings = get_settings()

    # Build pipeline
    logger.info("lifespan_startup_begin")
    pipeline = await build_mrag_pipeline()
    app.state.pipeline = pipeline

    # Database
    db_url = settings.database_url.get_secret_value()
    db_engine = create_db_engine(db_url, echo=settings.db_echo)
    db_session_factory = create_session_factory(db_engine)
    app.state.db_engine = db_engine
    app.state.db_session_factory = db_session_factory

    # Create tables
    await create_tables(db_engine)

    # Evaluation runner
    evaluator = EvaluationRunner(pipeline=pipeline, settings=settings)
    app.state.evaluator = evaluator

    # Startup timestamp for uptime calculation
    app.state.startup_ts = time.time()

    logger.info("lifespan_startup_complete")

    yield

    # Shutdown
    logger.info("lifespan_shutdown_begin")
    await db_engine.dispose()
    logger.info("lifespan_shutdown_complete")


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="MRAG API",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handler + access logging
    register_middleware(app)

    # Routes
    app.include_router(ask_router)
    app.include_router(health_router)
    app.include_router(evaluate_router)
    app.include_router(analytics_router)

    return app
