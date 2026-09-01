from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    title: str


class DocumentCreate(DocumentBase):
    pass


class DocumentChunkResponse(BaseModel):
    id: UUID
    page_number: int
    chapter: str | None
    section: str | None
    content: str

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    id: UUID
    file_path: str
    file_size: int
    status: str
    error_message: str | None
    uploaded_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


class DocumentWithChunks(DocumentResponse):
    chunks: list[DocumentChunkResponse] = []

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: UUID
    title: str
    message: str = "Document uploaded successfully. Processing in background."
