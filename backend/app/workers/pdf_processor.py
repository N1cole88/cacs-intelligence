import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from celery import Task
from app.workers.celery_app import celery_app
from app.db.session import async_session_factory
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.services.document_service import get_document_service
from app.services.embedding_service import get_embedding_service
from asgiref.sync import async_to_sync


@celery_app.task(bind=True)
def process_document(self: Task, document_id: str):
    """Process uploaded PDF: parse, chunk, and generate embeddings."""
    doc_uuid = uuid.UUID(document_id)
    async_to_sync(_process_document_async)(doc_uuid)


async def _process_document_async(document_id: uuid.UUID):
    """Async implementation of document processing."""
    async with async_session_factory() as db:
        # Get document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        try:
            # Update status
            document.status = "processing"
            await db.commit()
            # Parse PDF
            doc_service = get_document_service()
            embed_service = get_embedding_service()

            chunks_to_create = []

            for page_chunk in doc_service.parse_pdf(document.file_path):
                # Generate embedding
                embedding = await embed_service.embed_text(page_chunk.content)

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
            document.processed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            document.status = "failed"
            document.error_message = str(e)
            await db.commit()
            raise
