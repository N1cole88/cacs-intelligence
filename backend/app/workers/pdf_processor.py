import uuid
from datetime import datetime
from sqlalchemy import select
from celery import Task
from app.workers.celery_app import celery_app
from app.db.session import async_session_factory
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.document_service import get_document_service
from app.config import get_settings
import httpx

settings = get_settings()


@celery_app.task(bind=True)
def process_document(self: Task, document_id: str):
    """Process uploaded PDF: parse, chunk, and generate embeddings."""
    doc_uuid = uuid.UUID(document_id)
    process_document_sync(doc_uuid)


def process_document_sync(document_id: uuid.UUID, file_path: str = None):
    """Synchronous version for inline processing."""
    import asyncio
    asyncio.run(_process_document_async(document_id, file_path))


async def _process_document_async(document_id: uuid.UUID, file_path: str = None):
    """Async implementation of document processing."""
    async with async_session_factory() as db:
        # Get document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Use provided file_path or fall back to document's path
        pdf_path = file_path or document.file_path

        try:
            # Update status
            document.status = "processing"
            await db.commit()

            # Parse PDF
            doc_service = get_document_service()

            chunks_to_create = []

            for page_chunk in doc_service.parse_pdf(pdf_path):
                # Generate embedding using httpx (sync)
                try:
                    response = httpx.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={
                            "Authorization": f"Bearer {settings.openai_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "input": page_chunk.content[:8000],
                            "model": settings.embedding_model
                        },
                        timeout=30.0
                    )
                    embedding = response.json()["data"][0]["embedding"]
                except Exception as e:
                    print(f"Failed to generate embedding: {e}")
                    embedding = None

                chunk = DocumentChunk(
                    document_id=document.id,
                    page_number=page_chunk.page_number,
                    chapter=page_chunk.chapter,
                    section=page_chunk.section,
                    content=page_chunk.content,
                    embedding=embedding,
                )
                chunks_to_create.append(chunk)

            # Bulk insert chunks
            db.add_all(chunks_to_create)

            # Update document status
            document.status = "completed"
            document.processed_at = datetime.utcnow()
            await db.commit()

        except Exception as e:
            document.status = "failed"
            document.error_message = str(e)
            await db.commit()
            raise
