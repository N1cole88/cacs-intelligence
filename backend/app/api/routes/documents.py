import uuid
import os
import logging
from datetime import datetime
from typing import Annotated
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.config import get_settings
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])
settings = get_settings()

_executor = ThreadPoolExecutor(max_workers=2)


def _process_document_task(document_id: uuid.UUID, file_path: str):
    """Run async processing in a new thread with its own event loop."""
    import asyncio

    async def _process():
        from app.workers.pdf_processor import _process_document_async
        await _process_document_async(document_id, file_path)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_process())
    finally:
        loop.close()


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF file")],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Validate MIME type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    # Generate unique ID and save file
    doc_id = uuid.uuid4()
    file_ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{doc_id}{file_ext}"

    # Create uploads directory if needed (local storage for MVP)
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)

    # Save file
    content = await file.read()

    # Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 50MB)")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create database record
    document = Document(
        id=doc_id,
        title=file.filename,
        file_path=file_path,
        file_size=len(content),
        status="processing",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Process document in thread pool (to avoid event loop issues)
    try:
        future = _executor.submit(_process_document_task, document.id, file_path)
        future.result(timeout=120)  # Wait for completion (max 2 minutes)
        document.status = "completed"
        await db.commit()
    except Exception as e:
        logger.warning(f"Could not process document {document.id}: {e}")
        document.status = "failed"
        document.error_message = str(e)
        await db.commit()

    return DocumentUploadResponse(id=document.id, title=document.title)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Document).order_by(Document.uploaded_at.desc()))
    documents = result.scalars().all()
    return documents


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{doc_id}")
async def delete_document(doc_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete a document and its chunks."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk if exists
    if document.file_path:
        try:
            import os
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            logger.warning(f"Could not delete file {document.file_path}: {e}")

    # Delete from database (chunks will be cascade deleted)
    await db.delete(document)
    await db.commit()

    return {"message": "Document deleted successfully"}
