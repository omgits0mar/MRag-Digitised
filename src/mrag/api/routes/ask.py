"""POST /ask-question route.

Processes a user question through the full RAG pipeline and returns
a structured answer with citations, confidence, and timing.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from mrag.api.dependencies import (
    get_conversation_repo,
    get_pipeline,
    get_query_repo,
)
from mrag.api.schemas import (
    ErrorEnvelope,
    QuestionRequest,
    QuestionResponse,
    SourceResponse,
)
from mrag.db.repositories import ConversationRepository, QueryRepository
from mrag.db.utils import safe_persist
from mrag.pipeline import MRAGPipeline

router = APIRouter(tags=["ask"])


@router.post(
    "/ask-question",
    response_model=QuestionResponse,
    responses={422: {"model": ErrorEnvelope}, 500: {"model": ErrorEnvelope}},
    summary="Submit a question and receive an AI-generated answer",
)
async def ask_question(
    body: QuestionRequest,
    pipeline: MRAGPipeline = Depends(get_pipeline),
    query_repo: QueryRepository = Depends(get_query_repo),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
) -> QuestionResponse:
    """Process a question through the full RAG pipeline.

    Flow:
        1. Load conversation history if conversation_id present.
        2. Run MRAGPipeline.ask() with the question.
        3. Persist QueryRecord + ConversationTurn via safe_persist.
        4. Return QuestionResponse.
    """
    # Step 1: Load conversation history if provided
    conversation_history = None
    if body.conversation_id:
        turns = await conv_repo.get_recent_turns(body.conversation_id)
        # Convert ConversationTurn ORM objects to query.models.ConversationTurn
        from mrag.query.models import ConversationTurn as QueryTurn

        conversation_history = [
            QueryTurn(role="user", content=t.query_text) for t in turns
        ]

    # Step 2: Run pipeline
    response = await pipeline.ask(
        query=body.question,
        expand=body.expand,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        conversation_history=conversation_history,
    )

    # Step 3: Map to API response
    sources = [
        SourceResponse(
            chunk_id=s.chunk_id,
            doc_id=s.doc_id,
            text=s.chunk_text,
            relevance_score=s.relevance_score,
        )
        for s in response.sources
    ]

    result = QuestionResponse(
        answer=response.answer,
        confidence_score=response.confidence_score,
        is_fallback=response.is_fallback,
        sources=sources,
        response_time_ms=response.metrics.total_time_ms,
        conversation_id=body.conversation_id,
    )

    # Step 4: Persist QueryRecord (non-blocking)
    await safe_persist(
        query_repo.create(
            query_text=body.question,
            response_text=response.answer,
            confidence_score=response.confidence_score,
            is_fallback=response.is_fallback,
            total_time_ms=response.metrics.total_time_ms,
            cache_hit=response.metrics.cache_hit,
            embedding_time_ms=response.metrics.embedding_time_ms or None,
            search_time_ms=response.metrics.search_time_ms or None,
            llm_time_ms=response.metrics.llm_time_ms or None,
            conversation_id=body.conversation_id,
        ),
        operation="persist_query",
    )

    # Step 5: Persist ConversationTurn if conversation_id present
    if body.conversation_id:
        await safe_persist(
            conv_repo.create_turn(
                conversation_id=body.conversation_id,
                query_text=body.question,
                response_text=response.answer,
            ),
            operation="persist_conversation_turn",
        )

    return result
