"""POST /upload and GET /upload/status routes.

Accepts a multipart file upload, streams it to disk with a configurable
size cap, parses + chunks + embeds the content, and appends the new
vectors to the live FAISS index and metadata store.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from mrag.api.schemas import ErrorEnvelope, UploadResponse, UploadStatusResponse
from mrag.ingestion import FileTooLargeError, UploadIngestionError, UploadService

router = APIRouter(tags=["upload"])


async def get_upload_service(request: Request) -> UploadService:
    service = getattr(request.app.state, "upload_service", None)
    if service is None:
        raise HTTPException(
            status_code=503, detail="upload service not initialised"
        )
    return service


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        415: {"model": ErrorEnvelope},
        500: {"model": ErrorEnvelope},
    },
    summary="Upload a document and ingest it into the retrieval index",
)
async def upload_file(
    file: UploadFile = File(...),
    service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    filename = file.filename or "upload"
    try:
        service.validate_extension(filename)
    except UploadIngestionError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    try:
        saved_path = await service.save_stream(file, filename)
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    finally:
        await file.close()

    try:
        result = await service.ingest(saved_path, filename)
    except UploadIngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadResponse(**result.to_dict())


@router.get(
    "/upload/status",
    response_model=UploadStatusResponse,
    summary="Return index size and most recent upload metadata",
)
async def upload_status(
    service: UploadService = Depends(get_upload_service),
) -> UploadStatusResponse:
    last = service.last_result
    return UploadStatusResponse(
        total_vectors=service.total_vectors,
        allowed_extensions=service.allowed_extensions,
        max_bytes=service.max_bytes,
        last_upload=UploadResponse(**last.to_dict()) if last else None,
    )
