# CACS Intelligence P0 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational platform: Next.js frontend + FastAPI backend + PostgreSQL with pgvector + PDF upload + RAG chat

**Architecture:** 
- Modular monolith backend with service-oriented architecture
- Next.js 15 with App Router for frontend
- PostgreSQL with pgvector for document storage and semantic search
- S3-compatible storage for PDFs
- Background job processing via Celery

**Tech Stack:** Next.js 15, React, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy 2.0, PostgreSQL, pgvector, Redis, Celery, MinIO, OpenAI-compatible AI

---

## File Structure

```
CACS-learning/
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Settings
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── documents.py    # PDF upload endpoints
│   │   │       └── chat.py         # RAG chat endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── security.py         # Simple auth (personal use)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # SQLAlchemy base
│   │   │   └── session.py          # DB session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py         # Document model
│   │   │   └── chunk.py            # DocumentChunk model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── document.py         # Document schemas
│   │   │   └── chat.py             # Chat schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_service.py # PDF handling
│   │   │   ├── embedding_service.py # Embeddings
│   │   │   └── rag_service.py      # RAG retrieval
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_processor.py    # Celery tasks
│   │   │   └── celery_app.py       # Celery config
│   │   └── prompts/
│   │       ├── __init__.py
│   │       └── rag_system.txt      # RAG prompt
│   ├── requirements.txt
│   ├── alembic.ini
│   └── alembic/
│       ├── env.py
│       └── versions/
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── postcss.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx           # Dashboard
│   │   │   ├── globals.css
│   │   │   ├── chat/
│   │   │   │   └── page.tsx       # RAG chat page
│   │   │   └── api/
│   │   │       └── chat/
│   │   │           └── route.ts    # Chat API proxy
│   │   ├── components/
│   │   │   ├── ui/               # shadcn components
│   │   │   ├── chat/
│   │   │   │   ├── chat-window.tsx
│   │   │   │   └── message.tsx
│   │   │   └── dashboard/
│   │   │       └── stat-card.tsx
│   │   ├── lib/
│   │   │   ├── api.ts            # API client
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts
│   └── public/
└── docs/
    └── superpowers/
        └── specs/
```

---

## Backend Implementation

### Task 1: Backend Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/alembic.ini`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`

- [ ] **Step 1: Create backend/requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
pydantic==2.10.0
pydantic-settings==2.6.0
httpx==0.28.0
python-multipart==0.0.17
pymupdf==1.25.0
openai==1.58.0
redis==5.2.0
celery[redis]==5.4.0
pytest==8.3.4
pytest-asyncio==0.25.2
aioresponses==0.7.8
pgvector==0.3.1
asgiref==3.8.1
boto3==1.35.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Create backend/alembic.ini**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost:5432/cacs

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: Create backend/app/config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "CACS Intelligence"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cacs"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # S3 / MinIO
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "cacs-documents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_secure: bool = False
    
    # AI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Create backend/app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize connections
    settings = get_settings()
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="CACS Intelligence API",
    description="Personal AI learning platform for CACS exam prep",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "CACS Intelligence API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
```

- [ ] **Step 5: Commit**

```bash
cd backend
git init
git add -A
git commit -m "feat: scaffold backend project structure"
```

---

### Task 2: Database Models

**Files:**
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/document.py`
- Create: `backend/app/models/chunk.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/document.py`

- [ ] **Step 1: Create backend/app/db/base.py**

```python
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


# Import all models to register them
from app.models import document, chunk  # noqa: F401, E402
```

- [ ] **Step 2: Create backend/app/db/session.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import get_settings


settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **Step 3: Create backend/app/models/document.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
```

- [ ] **Step 4: Create backend/app/models/chunk.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import vector
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter: Mapped[str | None] = mapped_column(String(500), nullable=True)
    section: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(vector(1536), nullable=True)  # 1536 for text-embedding-3-small
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_document_id", "document_id"),
        Index("ix_document_chunks_chapter", "chapter"),
    )
```

- [ ] **Step 5: Create backend/app/schemas/document.py**

```python
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
```

- [ ] **Step 6: Run tests to verify imports work**

```bash
cd backend
python -c "from app.db.base import Base; from app.models import document, chunk; print('Models OK')"
```

- [ ] **Step 7: Set up pgvector extension and create migrations**

```bash
# Enable pgvector extension (connect to PostgreSQL first)
psql -h localhost -U postgres -d cacs -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Initialize Alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "create documents and chunks tables"

# Run migrations
alembic upgrade head
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/db/ backend/app/models/ backend/app/schemas/
git commit -m "feat: add database models for document and chunk"
```

---

### Task 3: Document Upload API

**Files:**
- Create: `backend/app/api/routes/documents.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create backend/app/api/routes/documents.py**

```python
import uuid
import os
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.config import get_settings

router = APIRouter(prefix="/api/documents", tags=["documents"])
settings = get_settings()


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
    with open(file_path, "wb") as f:
        f.write(content)

    # Create database record
    document = Document(
        id=doc_id,
        title=file.filename,
        file_path=file_path,
        file_size=len(content),
        status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Queue background job for processing
    from app.workers.pdf_processor import process_document
    process_document.delay(str(document.id))

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
```

- [ ] **Step 2: Modify backend/app/main.py to include routers**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.routes import documents, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    yield


app = FastAPI(
    title="CACS Intelligence API",
    description="Personal AI learning platform for CACS exam prep",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    return {"message": "CACS Intelligence API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
```

- [ ] **Step 3: Create placeholder chat router**

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(message: str):
    return {"response": "Chat endpoint - to be implemented"}
```

- [ ] **Step 4: Test the endpoint**

```bash
cd backend
uvicorn app.main:app --reload &
# Wait for startup, then test:
curl http://localhost:8000/health
curl http://localhost:8000/api/documents
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add document upload API endpoints"
```

---

### Task 4: PDF Processing Worker

**Files:**
- Create: `backend/app/workers/celery_app.py`
- Create: `backend/app/workers/pdf_processor.py`
- Create: `backend/app/services/embedding_service.py`
- Create: `backend/app/services/document_service.py`

- [ ] **Step 1: Create backend/app/workers/celery_app.py**

```python
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "cacs_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.pdf_processor"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
)
```

- [ ] **Step 2: Create backend/app/services/embedding_service.py**

```python
from openai import AsyncOpenAI
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.embedding_model

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
```

- [ ] **Step 3: Create backend/app/services/document_service.py**

```python
import pymupdf
from typing import Iterator
from dataclasses import dataclass


@dataclass
class PageChunk:
    page_number: int
    chapter: str | None
    section: str | None
    content: str


class DocumentService:
    """Service for parsing and chunking PDF documents."""

    def parse_pdf(self, file_path: str) -> Iterator[PageChunk]:
        """Parse PDF and yield chunks for each page."""
        doc = pymupdf.open(file_path)
        
        current_chapter = None
        current_section = None

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            
            # Simple heuristic: first line in large font = chapter heading
            # This is a basic implementation - can be enhanced
            lines = text.split("\n")
            clean_lines = [l.strip() for l in lines if l.strip()]
            
            if clean_lines:
                # Check for chapter headings (simple heuristic)
                first_line = clean_lines[0]
                if len(first_line) < 100 and first_line.isupper():
                    current_chapter = first_line
                
                content = "\n".join(clean_lines[1:]) if len(clean_lines) > 1 else text
            
            yield PageChunk(
                page_number=page_num,
                chapter=current_chapter,
                section=current_section,
                content=content if 'content' in locals() else text,
            )

        doc.close()

    def chunk_text(self, text: str, max_chars: int = 2000) -> list[str]:
        """Split text into smaller chunks."""
        # Simple chunking by paragraphs
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


def get_document_service() -> DocumentService:
    return DocumentService()
```

- [ ] **Step 4: Create backend/app/workers/pdf_processor.py**

```python
import uuid
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

        # Update status
        document.status = "processing"
        await db.commit()

        try:
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
            from datetime import datetime
            document.processed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            document.status = "failed"
            document.error_message = str(e)
            await db.commit()
            raise
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/workers/ backend/app/services/
git commit -m "feat: add PDF processing worker and services"
```

---

### Task 5: RAG Service & Chat API

**Files:**
- Create: `backend/app/services/rag_service.py`
- Create: `backend/app/prompts/rag_system.txt`
- Create: `backend/app/schemas/chat.py`
- Modify: `backend/app/api/routes/chat.py`

- [ ] **Step 1: Create backend/app/prompts/rag_system.txt`

```
You are a helpful tutor helping a student learn for the CACS (Certified Anti-Money Laundering Specialist) exam.
Your role is to explain concepts clearly, provide intuitive understanding, and connect theory to real-world scenarios.

Guidelines:
- Always ground your answers in the provided context from the study materials
- When citing sources, reference the page number and document title
- If the context doesn't contain enough information to answer the question, say so clearly
- Use clear explanations with practical examples where possible
- Break down complex concepts into digestible parts
- Connect concepts to real-world AML/compliance scenarios when relevant
```

- [ ] **Step 2: Create backend/app/schemas/chat.py**

```python
from pydantic import BaseModel, Field
from uuid import UUID


class ChatMessage(BaseModel):
    message: str = Field(..., description="User's question")


class SourceReference(BaseModel):
    document_title: str
    page_number: int
    content: str


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceReference] = []
```

- [ ] **Step 3: Create backend/app/services/rag_service.py**

```python
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from pgvector.sqlalchemy import vector
from app.config import get_settings
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.chat import ChatResponse, SourceReference
from pgvector.sqlalchemy import vector

settings = get_settings()


class RAGService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.chat_model = settings.chat_model

    async def retrieve_relevant_chunks(
        self, 
        db: AsyncSession, 
        query: str, 
        top_k: int = 5
    ) -> list[DocumentChunk]:
        """Retrieve relevant document chunks using semantic search."""
        # Generate query embedding
        embed_response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=query,
        )
        query_embedding = embed_response.data[0].embedding

        # Search using pgvector - cosine similarity
        # Note: This requires pgvector extension to be enabled
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def generate_response(
        self,
        query: str,
        retrieved_chunks: list[DocumentChunk],
    ) -> str:
        """Generate response using RAG pattern."""
        # Build context from retrieved chunks
        context_parts = []
        for chunk in retrieved_chunks:
            doc_title = chunk.document.title if chunk.document else "Unknown"
            context_parts.append(
                f"[Document: {doc_title}, Page {chunk.page_number}]\n{chunk.content}"
            )
        
        context = "\n\n---\n\n".join(context_parts)

        # Load system prompt
        import os
        prompt_dir = os.path.dirname(__file__).replace("\\", "/").replace("/services", "/prompts")
        system_prompt_path = os.path.join(prompt_dir, "rag_system.txt")
        with open(system_prompt_path, "r") as f:
            system_prompt = f.read()

        # Generate response
        response = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    async def chat(self, db: AsyncSession, message: str) -> ChatResponse:
        """Full RAG pipeline: retrieve + generate."""
        # Retrieve relevant chunks
        chunks = await self.retrieve_relevant_chunks(db, message)
        
        if not chunks:
            return ChatResponse(
                response="No relevant information found in your documents. Please upload some CACS study materials first.",
                sources=[],
            )

        # Generate response
        response_text = await self.generate_response(message, chunks)

        # Build sources
        sources = []
        seen_docs = set()
        for chunk in chunks:
            doc_title = chunk.document.title if chunk.document else "Unknown"
            if doc_title not in seen_docs:
                sources.append(
                    SourceReference(
                        document_title=doc_title,
                        page_number=chunk.page_number,
                        content=chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
                    )
                )
                seen_docs.add(doc_title)

        return ChatResponse(response=response_text, sources=sources)


def get_rag_service() -> RAGService:
    return RAGService()
```

- [ ] **Step 4: Modify backend/app/api/routes/chat.py**

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.rag_service import get_rag_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """RAG-powered chat endpoint."""
    rag_service = get_rag_service()
    return await rag_service.chat(db, message.message)
```

- [ ] **Step 5: Test the chat endpoint**

```bash
# Restart backend and test:
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is money laundering?"}'
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/rag_service.py backend/app/prompts/ backend/app/schemas/chat.py backend/app/api/routes/chat.py
git commit -m "feat: add RAG service and chat API endpoint"
```

---

### Task 6: Frontend Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/next.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "cacs-intelligence-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "next": "15.1.0",
    "@tanstack/react-query": "^5.62.0",
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.24.0",
    "lucide-react": "^0.468.0",
    "recharts": "^2.14.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",
    "class-variance-authority": "^0.7.1"
  },
  "devDependencies": {
    "@types/node": "^22.10.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.7.0",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "eslint": "^9.17.0",
    "eslint-config-next": "15.1.0",
    "autoprefixer": "^10.4.20"
  }
}
```

- [ ] **Step 2: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Create frontend/tailwind.config.ts**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(214.3 31.8% 91.4%)",
        input: "hsl(214.3 31.8% 91.4%)",
        ring: "hsl(222.2 84% 4.9%)",
        background: "hsl(0 0% 100%)",
        foreground: "hsl(222.2 84% 4.9%)",
        primary: {
          DEFAULT: "hsl(222.2 47.4% 11.2%)",
          foreground: "hsl(210 40% 98%)",
        },
        secondary: {
          DEFAULT: "hsl(210 40% 96.1%)",
          foreground: "hsl(222.2 47.4% 11.2%)",
        },
        muted: {
          DEFAULT: "hsl(210 40% 96.1%)",
          foreground: "hsl(215.4 16.3% 46.9%)",
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 4: Create frontend/next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [],
  },
};

module.exports = nextConfig;
```

- [ ] **Step 5: Create frontend/postcss.config.js**

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 6: Create frontend/src/app/globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

- [ ] **Step 7: Create frontend/src/app/layout.tsx**

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CACS Intelligence",
  description: "Personal AI learning platform for CACS exam prep",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 8: Create frontend/src/components/providers.tsx**

```typescript
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
```

- [ ] **Step 9: Create frontend/src/app/page.tsx (Dashboard)**

```typescript
import { FileText, MessageSquare, BarChart3, BookOpen } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">CACS Intelligence</h1>
          <p className="mt-1 text-gray-600">Your AI-powered learning companion</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Document Upload */}
          <a
            href="/documents"
            className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow"
          >
            <FileText className="h-10 w-10 text-blue-600 mb-4" />
            <h3 className="text-lg font-semibold">Documents</h3>
            <p className="text-sm text-gray-600 mt-1">Upload CACS study materials</p>
          </a>

          {/* Chat */}
          <a
            href="/chat"
            className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow"
          >
            <MessageSquare className="h-10 w-10 text-green-600 mb-4" />
            <h3 className="text-lg font-semibold">Ask Questions</h3>
            <p className="text-sm text-gray-600 mt-1">Chat with your study materials</p>
          </a>

          {/* Practice */}
          <a
            href="/practice"
            className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow"
          >
            <BookOpen className="h-10 w-10 text-purple-600 mb-4" />
            <h3 className="text-lg font-semibold">Practice</h3>
            <p className="text-sm text-gray-600 mt-1">Test your knowledge</p>
          </a>

          {/* Progress */}
          <a
            href="/progress"
            className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow"
          >
            <BarChart3 className="h-10 w-10 text-orange-600 mb-4" />
            <h3 className="text-lg font-semibold">Progress</h3>
            <p className="text-sm text-gray-600 mt-1">Track your mastery</p>
          </a>
        </div>

        {/* Quick Stats */}
        <div className="mt-12">
          <h2 className="text-xl font-semibold mb-4">Getting Started</h2>
          <div className="bg-white rounded-lg border p-6">
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Upload your CACS study materials (PDF)</li>
              <li>Wait for processing to complete</li>
              <li>Start chatting with your documents</li>
              <li>Track your progress as you learn</li>
            </ol>
          </div>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 10: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Next.js frontend"
```

---

### Task 7: Chat UI Page

**Files:**
- Create: `frontend/src/app/chat/page.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: Create frontend/src/types/index.ts**

```typescript
export interface Document {
  id: string;
  title: string;
  file_path: string;
  file_size: number;
  status: string;
  error_message: string | null;
  uploaded_at: string;
  processed_at: string | null;
}

export interface SourceReference {
  document_title: string;
  page_number: number;
  content: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
}
```

- [ ] **Step 2: Create frontend/src/lib/api.ts`

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadDocument(file: File): Promise<{ id: string; title: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/api/documents`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Failed to upload document");
  }

  return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${API_URL}/api/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function chat(message: string) {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}
```

- [ ] **Step 3: Create frontend/src/app/chat/page.tsx**

```typescript
"use client";

import { useState } from "react";
import { Send, FileText, User, Bot } from "lucide-react";
import { chat } from "@/lib/api";
import type { ChatMessage, SourceReference } from "@/types";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hello! I'm your CACS study assistant. Upload your study materials and ask me anything about the concepts.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await chat(userMessage);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.response,
          sources: response.sources,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-bold">Chat with your materials</h1>
          <p className="text-sm text-gray-600">Ask questions about CACS concepts</p>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full p-4 flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-green-600" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white border"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t text-sm">
                    <p className="font-semibold mb-2">Sources:</p>
                    {msg.sources.map((source: SourceReference, j: number) => (
                      <div key={j} className="text-xs mb-2">
                        <span className="font-medium">{source.document_title}</span>
                        <span className="text-gray-500"> (page {source.page_number})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-blue-600" />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                <Bot className="w-5 h-5 text-green-600" />
              </div>
              <div className="bg-white border rounded-lg p-3">
                <p className="text-gray-500">Thinking...</p>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 p-3 border rounded-lg"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/chat/ frontend/src/lib/ frontend/src/types/
git commit -m "feat: add chat UI page"
```

---

### Task 8: Document Upload UI

**Files:**
- Create: `frontend/src/app/documents/page.tsx`

- [ ] **Step 1: Create frontend/src/app/documents/page.tsx**

```typescript
"use client";

import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { uploadDocument, listDocuments } from "@/lib/api";
import type { Document } from "@/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const doc = await uploadDocument(file);
      setDocuments((prev) => [
        {
          id: doc.id,
          title: doc.title,
          file_path: "",
          file_size: file.size,
          status: "pending",
          error_message: null,
          uploaded_at: new Date().toISOString(),
          processed_at: null,
        },
        ...prev,
      ]);
    } catch (error) {
      alert("Failed to upload document");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Loader2 className="w-5 h-5 text-yellow-600 animate-spin" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-bold">Documents</h1>
          <p className="text-sm text-gray-600">Upload your CACS study materials</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4">
        {/* Upload Area */}
        <div className="bg-white rounded-lg border p-6 mb-6">
          <label className="flex flex-col items-center justify-center cursor-pointer">
            <Upload className="w-10 h-10 text-gray-400 mb-2" />
            <span className="text-gray-600">
              {uploading ? "Uploading..." : "Click to upload PDF"}
            </span>
            <span className="text-sm text-gray-400">PDF files only</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>

        {/* Document List */}
        <div className="bg-white rounded-lg border">
          <div className="px-6 py-4 border-b">
            <h2 className="font-semibold">Your Documents</h2>
          </div>
          {documents.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No documents uploaded yet
            </div>
          ) : (
            <div className="divide-y">
              {documents.map((doc) => (
                <div key={doc.id} className="px-6 py-4 flex items-center gap-4">
                  <FileText className="w-8 h-8 text-gray-400" />
                  <div className="flex-1">
                    <p className="font-medium">{doc.title}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                  {getStatusIcon(doc.status)}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/documents/
git commit -m "feat: add document upload UI"
```

---

### Task 9: Docker Compose Setup

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
version: "3.8"

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: cacs
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/cacs
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      S3_BUCKET: cacs-documents
      S3_ACCESS_KEY: minioadmin
      S3_SECRET_KEY: minioadmin
      S3_SECURE: "false"
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - uploads:/app/uploads

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
  minio_data:
  uploads:
```

- [ ] **Step 2: Create .env.example**

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cacs

# Redis
REDIS_URL=redis://localhost:6379/0

# S3 / MinIO
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=cacs-documents
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_SECURE=false

# AI
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# App
APP_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 3: Create backend Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create frontend/Dockerfile**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

CMD ["npm", "start"]
```

- [ ] **Step 5: Create postgres-init directory and enable pgvector**

```bash
# Create postgres-init directory
mkdir -p postgres-init

# Create init script to enable pgvector extension
cat > postgres-init/01-enable-pgvector.sql << 'EOF'
CREATE EXTENSION IF NOT EXISTS vector;
EOF
```

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml .env.example backend/Dockerfile frontend/Dockerfile postgres-init/
git commit -m "feat: add Docker Compose setup for local development"
```

---

## Summary

This plan implements P0 of the CACS Intelligence platform:

| Task | Description |
|------|-------------|
| 1 | Backend project setup |
| 2 | Database models (Document, DocumentChunk) |
| 3 | Document upload API |
| 4 | PDF processing worker |
| 5 | RAG service & chat API |
| 6 | Frontend scaffold |
| 7 | Chat UI page |
| 8 | Document upload UI |
| 9 | Docker Compose setup |

After completing P0, you'll have a working MVP where:
- Users can upload PDF documents
- Documents are parsed and chunked
- Chunks are embedded for semantic search
- Users can chat with their documents and get cited answers
