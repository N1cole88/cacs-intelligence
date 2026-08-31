# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CACS Intelligence is a personal AI-powered learning platform for CACS (Certified Anti-Money Laundering Specialist) exam preparation. It turns CACS study materials into a connected knowledge base and links them to real-world financial news.

## Technology Stack

- **Frontend**: Next.js 15+, React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Recharts
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic
- **Database**: PostgreSQL 16+ with pgvector
- **Storage**: S3-compatible (MinIO local, AWS S3 production)
- **Queue**: Redis + Celery
- **AI**: OpenAI-compatible provider abstraction

## Architecture

Modular monolith structure:
- `backend/app/` - FastAPI application with services for documents, RAG, concepts, knowledge_graph, news, practice, mastery, AI
- `frontend/` - Next.js 15 with App Router

Key services:
- Document ingestion pipeline (PDF → chunks → embeddings)
- RAG retrieval with hybrid search (semantic + keyword)
- Knowledge graph (concepts + relationships)
- News pipeline (ingest → classify → match → score)
- Practice engine (question generation from concepts)
- Mastery tracking

## Development Commands

```bash
# Start all services (requires Docker)
docker-compose up -d

# Backend development
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
npm run dev

# Run tests
pytest                    # Backend
npm run test             # Frontend
```

## Key Patterns

- Background jobs are async via Celery (not synchronous HTTP)
- All AI outputs validated with Pydantic schemas
- Prompts stored in versioned files (`backend/app/prompts/`)
- Per-chunk metadata retained for citations (document_id, page_number, chapter, section)
- Learning score combines: financial_importance × cacs_relevance × user_weakness × recency

## Implementation Priority

1. **P0**: Next.js + FastAPI + PostgreSQL + PDF upload + RAG chat
2. **P1**: Concept extraction + Knowledge graph + News matching
3. **P2**: Practice engine + Mastery tracking + Daily brief
4. **P3**: Visual knowledge map + Analytics
