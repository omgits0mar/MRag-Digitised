"""POST /ask-question route.

Processes a user question through the full RAG pipeline and returns
a structured answer with citations, confidence, and timing.

Persistence is performed in an independent session so that flush/commit
failures do not corrupt the read session or the API response.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from mrag.api.dependencies import (
    get_db_session,
    get_pipeline,
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


async def _persist_query_and_turn(
    request: Request,
    body: QuestionRequest,
    response,
) -> None:
    """Persist QueryRecord and ConversationTurn in an independent session.

    Uses its own session so failures never corrupt the read session.
    """
    session_factory = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            query_repo = QueryRepository(session)
            await query_repo.create(
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
            )

            if body.conversation_id:
                conv_repo = ConversationRepository(session)
                await conv_repo.create_turn(
                    conversation_id=body.conversation_id,
                    query_text=body.question,
                    response_text=response.answer,
                )

            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post(
    "/ask-question",
    response_model=QuestionResponse,
    responses={422: {"model": ErrorEnvelope}, 500: {"model": ErrorEnvelope}},
    summary="Submit a question and receive an AI-generated answer",
)
async def ask_question(
    request: Request,
    body: QuestionRequest,
    pipeline: MRAGPipeline = Depends(get_pipeline),
    read_session: AsyncSession = Depends(get_db_session),
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
        conv_repo = ConversationRepository(read_session)
        turns = await conv_repo.get_recent_turns(body.conversation_id)
        # Convert ConversationTurn ORM objects to query.models.ConversationTurn
        from mrag.query.models import ConversationTurn as QueryTurn

        conversation_history = [
            QueryTurn(
                query=t.query_text,
                response=t.response_text,
                timestamp=t.created_at.timestamp(),
            )
            for t in turns
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

    # Step 4: Persist in independent session (non-blocking on failure)
    await safe_persist(
        _persist_query_and_turn(request, body, response),
        operation="persist_query_and_turn",
    )

    return result
