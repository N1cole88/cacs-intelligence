# CACS Intelligence — Design Specification

## Project Overview

- **Name**: CACS Intelligence
- **Type**: Personal AI-powered learning platform for CACS (Certified Anti-Money Laundering Specialist) exam preparation
- **Target Users**: Finance/investment/private banking professionals
- **Scope**: Personal use only (single user)

## Core Features

1. **PDF Upload & Ingestion** — Upload multiple CACS PDFs over time; system parses, chunks, and embeds content
2. **Concept Extraction** — Automatically extract CACS concepts from materials and build a knowledge graph
3. **RAG Chat** — Ask questions and get answers grounded in the uploaded materials with citations
4. **News Ingestion** — Daily automated news fetching from financial sources
5. **News-CACS Matching** — AI-powered matching of news to CACS concepts with explanations
6. **Practice Questions** — Scenario-based quiz questions generated from concepts
7. **Mastery Tracking** — Track concept mastery and recommend review sessions
8. **Progress Dashboard** — Visual progress by chapter/concept

## Technology Stack

### Frontend
- Next.js 15+ (App Router)
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Lucide icons
- TanStack Query for server-state
- React Hook Form + Zod
- Recharts for analytics
- React Flow (P3 - knowledge graph visualization)

### Backend
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 (async)
- Alembic for migrations
- httpx for HTTP
- pytest

### Database
- PostgreSQL 16+ with pgvector
- Single-user mode: no multi-tenant isolation needed

### Storage
- S3-compatible object storage
- Local: MinIO
- Production: AWS S3

### Background Jobs
- Redis + Celery (or Dramatiq)
- Tasks: PDF ingestion, embedding generation, concept extraction, news pipeline, daily brief

### AI Layer
- Internal provider abstraction (`LLMProvider`)
- Support for OpenAI-compatible APIs
- Structured JSON output validated with Pydantic

## Architecture

### System Structure

```
                    ┌──────────────────────┐
                    │       Next.js        │
                    │      Frontend        │
                    └──────────┬───────────┘
                               │ HTTPS
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
     ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
     │ PostgreSQL  │   │    Redis      │   │ Object Store │
     │ + pgvector  │   │    Queue     │   │     S3       │
     └─────────────┘   └──────┬───────┘   └──────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │ Background      │
                      │ Workers         │
                      └─────────────────┘
```

### Backend Modules

```
backend/app/
  api/          # FastAPI routes
  core/         # Config, security
  db/           # SQLAlchemy setup
  models/       # ORM models
  schemas/      # Pydantic schemas
  services/
    documents/  # PDF handling
    rag/        # Retrieval
    concepts/   # Concept management
    knowledge_graph/
    news/       # News pipeline
    practice/   # Question generation
    mastery/    # Mastery calculations
    ai/         # LLM orchestration
  workers/      # Celery tasks
  prompts/      # Versioned prompts
```

### Frontend Structure

```
src/
  app/
    page.tsx           # Home/dashboard
    learn/             # Concept learning
    news/              # News feed
    practice/          # Quiz
    progress/          # Progress tracking
    chat/              # RAG chat
  components/
    ui/                # shadcn components
    dashboard/
    concepts/
    news/
    practice/
  lib/
    api/               # API client
    utils/
  hooks/
  types/
```

## Data Models

### Document
- id, title, file_path, uploaded_at, status
- Chunks: document_id, page_number, chapter, section, content, embedding

### Concept
- id, name, chapter, description, source_pages
- Relationships: source_concept_id, target_concept_id, relationship_type

### News
- id, title, url, published_at, content, source
- Concept matches: news_id, concept_id, relevance_score, reason

### Mastery
- concept_id, attempt_count, correct_count, last_attempt_at, last_correct_at

### Practice
- questions with type, difficulty, concept_id, content, options, correct_answer

## Key Algorithms

### News → CACS Matching
```
Article
   → Extract financial entities
   → Find candidate CACS concepts (semantic similarity)
   → LLM relevance judgment
   → Store: news_id, concept_id, score, reason
```

### Learning Score (News Ranking)
```
learning_score =
    financial_importance
    × cacs_relevance
    × user_weakness
    × recency
```

### Mastery Calculation (MVP)
```
mastery_score = correct_answers / total_attempts
```

## API Endpoints

```text
POST   /api/documents          # Upload PDF
GET    /api/documents          # List documents
GET    /api/documents/:id      # Get document

GET    /api/concepts           # List concepts
GET    /api/concepts/:id       # Get concept
GET    /api/concepts/:id/related

GET    /api/news               # Get daily news
GET    /api/news/:id          # Get article
POST   /api/news/analyze       # Trigger AI analysis

GET    /api/practice           # Get practice questions
POST   /api/practice/:id/attempt

GET    /api/progress           # Get mastery progress

POST   /api/chat               # RAG chat
```

## UI Flows

### Home Dashboard
- Continue Learning
- Today's CACS News
- Weak Concepts
- Quick Practice

### Learn Flow
Chapter → Concept → Definition → Intuition → Real-world example → Related concepts → Practice

### News Flow
Headline → What happened? → CACS concepts → Connection → Knowledge graph path → Investor implication → Exam question

### Practice Flow
Question → Answer → Explanation → Mastery update

### Progress Flow
Overall mastery → By chapter → By concept → Weaknesses → Recommended review

## Background Jobs

```text
process_document(document_id)       # Parse PDF, create chunks
extract_document_concepts(doc_id)   # Extract and link concepts
generate_embeddings(document_id)   # Create vector embeddings
fetch_news()                       # Fetch from all sources
deduplicate_news()                 # Remove duplicates
analyze_news(article_id)           # AI analysis
match_news_to_concepts(article_id) # Concept matching
generate_daily_brief()             # Create daily summary
```

## Daily Pipeline (07:00 Asia/Jakarta)

```
fetch all sources → normalize → deduplicate → classify → extract concepts → match CACS → calculate score → select top 3-5 → generate analysis → store brief
```

## Implementation Priority

### P0 — Foundation
1. Next.js frontend scaffold
2. FastAPI backend setup
3. PostgreSQL + pgvector
4. PDF upload to S3
5. Document parsing (PyMuPDF)
6. Chunking + embeddings
7. RAG chat with citations

### P1 — Knowledge Building
1. Concept extraction (LLM)
2. Knowledge graph data model
3. Concept pages
4. News ingestion (RSS feeds)
5. News → CACS matching

### P2 — Learning Features
1. Practice question generation
2. Quiz interface
3. Mastery tracking
4. Personalized review sessions
5. Daily brief generation

### P3 — Enhanced UI
1. Visual knowledge map (React Flow)
2. Advanced analytics
3. Additional news providers

## Environment Variables

```env
DATABASE_URL=
REDIS_URL=
S3_ENDPOINT=
S3_BUCKET=
S3_ACCESS_KEY=
S3_SECRET_KEY=
LLM_API_KEY=
EMBEDDING_API_KEY=
APP_ENV=
NEXT_PUBLIC_API_URL=
```

## Definition of Done

The MVP is complete when:
1. User uploads CACS PDF → system parses and indexes
2. System extracts CACS concepts → connects in graph
3. Daily news is ingested → matched to CACS concepts
4. User sees why news relates to CACS
5. User answers practice question → mastery updates
6. System recommends next review

Each stage should be replaceable without rewriting the entire application.
