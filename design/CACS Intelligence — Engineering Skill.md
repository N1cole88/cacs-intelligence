# CACS Intelligence — Engineering Skill

## Mission

Build and maintain CACS Intelligence: a personal AI learning system that turns CACS study material into a connected knowledge base and continuously links it to real-world financial news.

The primary learning loop is:

```text
CACS Material
     ↓
Concepts
     ↓
Knowledge Graph
     ↓
Real-World News
     ↓
Application
     ↓
Practice
     ↓
Mastery
     ↓
Personalized Review
```

The system must support three entry points:

```text
Material → Learn → Apply
News → Connect → Learn
Weakness → Review → Practice
```

---

# 1. Technology Stack

Use the following stack unless there is a strong technical reason to deviate.

## Frontend

- Next.js 15+
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide icons
- TanStack Query for server-state management
- React Hook Form + Zod for forms/validation
- Recharts for simple analytics
- React Flow for the knowledge graph

The frontend should be a responsive web application.

---

## Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- Alembic
- httpx
- pytest

The backend owns:

- authentication/session handling
- document ingestion
- RAG retrieval
- knowledge graph operations
- news ingestion
- concept matching
- AI orchestration
- practice generation
- mastery calculation

---

## Database

Use:

- PostgreSQL 16+
- pgvector

Use PostgreSQL as the primary system of record.

Do **not** introduce Neo4j for the MVP.

The knowledge graph is represented relationally using:

```text
concepts
concept_relationships
```

pgvector handles semantic retrieval.

---

## Object Storage

Use S3-compatible object storage for uploaded PDFs.

For local development:

- MinIO

For production:

- AWS S3 or equivalent

Never store large PDFs directly inside PostgreSQL.

---

## Background Jobs

Use a lightweight job system.

Preferred:

- Redis
- Celery or Dramatiq

Jobs include:

```text
PDF ingestion
Embedding generation
Concept extraction
News ingestion
News classification
News-to-CACS matching
Daily brief generation
```

Do not make these processes synchronous HTTP requests.

---

## Scheduling

Use a scheduled worker for daily news ingestion.

For MVP:

- Celery Beat

Alternative:

- application cron

The daily pipeline should be idempotent.

Example:

```text
07:00
 ↓
fetch news
 ↓
deduplicate
 ↓
classify
 ↓
match CACS concepts
 ↓
generate daily brief
```

---

## AI Layer

Create an internal provider abstraction:

```python
class LLMProvider:
    async def generate(...)
    async def generate_structured(...)
    async def embed(...)
```

Do not couple business logic directly to one model provider.

The application should support:

- structured JSON generation
- embeddings
- RAG
- tool calling

All AI outputs must be schema-validated with Pydantic.

---

## News Sources

The initial news layer should prioritize free sources.

Examples:

- Google News RSS
- Yahoo Finance feeds
- CNBC RSS
- Investing.com feeds
- Federal Reserve
- ECB
- Bank Indonesia
- MAS
- FRED
- SEC

Implement a common adapter:

```python
class NewsProvider(Protocol):
    async def fetch_articles(self) -> list[NewsArticle]:
        ...
```

Each source gets its own adapter.

Never make one provider a hard architectural dependency.

---

# 2. System Architecture

Use a modular monolith for MVP.

```text
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
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
            ▼                      ▼                      ▼
     ┌─────────────┐       ┌──────────────┐       ┌──────────────┐
     │ PostgreSQL  │       │    Redis     │       │ Object Store │
     │ + pgvector  │       │    Queue     │       │     S3       │
     └─────────────┘       └──────┬───────┘       └──────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Background      │
                         │ Workers         │
                         └────────┬────────┘
                                  │
               ┌──────────────────┼──────────────────┐
               │                  │                  │
               ▼                  ▼                  ▼
         PDF Pipeline        News Pipeline      AI Pipeline
```

Keep the backend as a modular monolith.

Recommended modules:

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
      documents/
      rag/
      concepts/
      knowledge_graph/
      news/
      practice/
      mastery/
      ai/
    workers/
    prompts/
```

---

# 3. Data Flow

## A. CACS Material Ingestion

```text
User uploads PDF
       ↓
Next.js
       ↓
POST /documents
       ↓
S3 / MinIO
       ↓
Create document record
       ↓
Queue ingestion job
       ↓
Parse PDF
       ↓
Extract pages
       ↓
Chunk content
       ↓
Extract chapter/section metadata
       ↓
Generate embeddings
       ↓
Store document_chunks
       ↓
Extract concepts
       ↓
Create concept relationships
```

Important:

Every chunk must retain:

```text
document_id
page_number
chapter
section
content
embedding
```

This is required for trustworthy citations.

---

# 4. RAG Architecture

Use hybrid retrieval when practical:

```text
User question
     ↓
Query understanding
     ↓
Semantic retrieval via pgvector
     +
Keyword/metadata filtering
     ↓
Top relevant chunks
     ↓
Related concepts
     ↓
User mastery
     ↓
LLM
```

Prioritize:

1. exact curriculum relevance
2. semantic relevance
3. source quality
4. user context

The model should not receive the entire CACS corpus.

---

# 5. Knowledge Graph Architecture

The graph consists of nodes and edges.

### Node

```text
Concept
```

Example:

```json
{
  "id": "duration",
  "name": "Duration",
  "chapter": "Fixed Income",
  "description": "...",
  "source_pages": [123, 124]
}
```

### Edge

```text
Concept A → relationship → Concept B
```

Example:

```json
{
  "source_concept_id": "interest_rates",
  "target_concept_id": "bond_prices",
  "relationship_type": "inverse_relationship"
}
```

Supported relationships:

```text
related_to
part_of
causes
affects
inverse_relationship
measured_by
prerequisite_of
example_of
```

The graph should support traversal such as:

```text
Inflation
 → Monetary Policy
 → Interest Rates
 → Bond Yields
 → Bond Prices
 → Duration
```

---

# 6. News Architecture

The News Service should be provider-agnostic.

```text
                    News Service
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Google RSS      CNBC RSS      Official Sources
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    Normalize
                         ↓
                    Deduplicate
                         ↓
                Financial Classifier
                         ↓
                  Concept Extraction
                         ↓
                 CACS Concept Matching
                         ↓
                 Relevance Scoring
                         ↓
                  Daily News Feed
```

---

# 7. News → CACS Matching

This is one of the core product algorithms.

For each article:

```text
Article
   ↓
financial entities/topics
   ↓
candidate CACS concepts
   ↓
semantic similarity
   +
knowledge graph relationship
   +
LLM relevance judgment
   ↓
concept relevance score
```

Store:

```text
news_id
concept_id
relevance_score
reason
```

The system should be able to explain:

> "This article is related to Duration because it discusses rising Treasury yields and the effect of rate changes on long-term bonds."

---

# 8. Personal Relevance Ranking

Do not simply sort by publication time.

Calculate a learning-oriented score:

```text
learning_score =
    financial_importance
    × cacs_relevance
    × user_weakness
    × recency
```

The exact weighting should be configurable.

Store the scoring components for debugging.

---

# 9. AI Orchestration

Create an AI orchestration service.

```text
AIService
├── explain_concept()
├── analyze_news()
├── generate_case()
├── generate_question()
├── explain_answer()
├── generate_review_session()
└── chat()
```

Each function should have:

- typed input
- typed output
- versioned prompt
- structured validation

Example:

```python
class NewsAnalysis(BaseModel):
    summary: str
    concepts: list[MatchedConcept]
    connection: str
    real_world_implication: str
    client_implication: str | None
    exam_connection: str
    common_trap: str | None
    question: ExamQuestion
```

---

# 10. Practice Engine

Practice questions are generated from:

```text
concept
+
difficulty
+
user mastery
+
recent mistakes
+
optional news context
```

Question types:

```text
concept recognition
scenario application
causal reasoning
calculation
comparison
client/portfolio scenario
```

Prioritize scenario-based questions.

---

# 11. Mastery Engine

For MVP:

```text
mastery_score =
correct_answers / total_attempts
```

Store additional fields:

```text
attempt_count
correct_count
last_attempt_at
last_correct_at
```

Later add:

- question difficulty
- recency decay
- repeated mistakes
- confidence
- response time

Do not present the score as a scientifically validated learning measurement.

Call it:

> Mastery estimate

---

# 12. API Design

Use REST for MVP.

Example endpoints:

```text
POST   /api/documents
GET    /api/documents
GET    /api/documents/:id

GET    /api/concepts
GET    /api/concepts/:id
GET    /api/concepts/:id/related

GET    /api/news
GET    /api/news/:id
POST   /api/news/analyze

GET    /api/practice
POST   /api/practice/:id/attempt

GET    /api/progress
GET    /api/review

POST   /api/chat
```

Use OpenAPI generated by FastAPI.

---

# 13. Frontend Architecture

Recommended:

```text
src/
  app/
    page.tsx
    learn/
    news/
    practice/
    knowledge/
    progress/
    chat/
  components/
    ui/
    dashboard/
    concepts/
    news/
    practice/
    knowledge/
  lib/
    api/
    utils/
  hooks/
  types/
```

Use server components where appropriate.

Use client components only where interactivity requires them.

Centralize API access.

Do not scatter raw fetch calls throughout components.

---

# 14. Main UI Flows

## Home

```text
Continue Learning
Today's CACS News
Weak Concepts
Quick Practice
Knowledge Map
```

## Learn

```text
Chapter
 ↓
Concept
 ↓
Definition
 ↓
Intuition
 ↓
Real-world example
 ↓
Related concepts
 ↓
Practice
```

## News

```text
Headline
 ↓
What happened?
 ↓
CACS concepts
 ↓
Connection
 ↓
Knowledge graph path
 ↓
Investor implication
 ↓
Exam question
```

## Practice

```text
Question
 ↓
Answer
 ↓
Explanation
 ↓
Mastery update
```

## Progress

```text
Overall mastery
 ↓
By chapter
 ↓
By concept
 ↓
Weaknesses
 ↓
Recommended review
```

---

# 15. Background Jobs

The following tasks should be asynchronous:

```text
process_document(document_id)
extract_document_concepts(document_id)
generate_embeddings(document_id)
fetch_news()
deduplicate_news()
analyze_news(article_id)
match_news_to_concepts(article_id)
generate_daily_brief()
```

Each job should be:

- retryable
- idempotent
- observable
- safe to rerun

---

# 16. Daily News Job

Default schedule:

```text
07:00 Asia/Jakarta
```

Flow:

```text
fetch all configured sources
       ↓
normalize articles
       ↓
deduplicate
       ↓
discard stale/irrelevant stories
       ↓
extract financial concepts
       ↓
match CACS concepts
       ↓
calculate learning score
       ↓
select top 3–5
       ↓
generate learning analysis
       ↓
store daily brief
```

The UI should show the latest successfully generated brief even if the current ingestion job fails.

---

# 17. Prompt Architecture

Store prompts in version-controlled files.

Example:

```text
prompts/
  concept_extraction_v1.txt
  news_classification_v1.txt
  news_cacs_mapping_v1.txt
  concept_explanation_v1.txt
  question_generation_v1.txt
  review_generation_v1.txt
```

Never bury important prompts directly inside controllers.

---

# 18. Observability

Log:

- request ID
- job ID
- model call
- prompt version
- latency
- token usage where available
- retrieval count
- source IDs
- errors

Never log:

- API keys
- private credentials
- unnecessary personal data
- full uploaded document contents

Add structured logging.

---

# 19. Testing Strategy

## Unit tests

Test:

- news deduplication
- relevance scoring
- mastery calculation
- concept relationship traversal
- parsing
- schema validation

## Integration tests

Test:

```text
PDF → chunks → embeddings → retrieval

News → concepts → CACS mapping

Question → answer → mastery update
```

## AI tests

Maintain a small evaluation dataset for:

- concept extraction
- news mapping
- grounded answers
- question quality

AI outputs should be checked for:

- unsupported claims
- fabricated sources
- wrong concept mappings
- invalid JSON

---

# 20. Security

Required:

- environment variables for secrets
- server-side AI calls
- server-side news API/RSS access
- authenticated document access
- per-user data isolation
- signed/private object URLs where needed
- input validation
- file type and file size limits

Never expose:

```text
LLM API keys
database credentials
news provider credentials
S3 credentials
```

to the browser.

---

# 21. MVP Deployment

Preferred simple deployment:

```text
Frontend:
Vercel

Backend:
Railway / Render / Fly.io

Database:
Managed PostgreSQL + pgvector

Redis:
Managed Redis

Storage:
S3-compatible object storage
```

Use Docker for local development and production consistency.

Provide:

```text
docker-compose.yml
```

for:

```text
postgres
redis
minio
backend
frontend
```

---

# 22. Environment Variables

Example:

```text
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

Never commit secrets.

Provide:

```text
.env.example
```

---

# 23. Engineering Constraints

Prefer:

```text
simple
typed
modular
observable
replaceable
```

Avoid:

```text
microservices
Neo4j
Kafka
Kubernetes
complex multi-agent systems
```

unless a concrete requirement emerges.

The MVP should be a **modular monolith**.

---

# 24. Implementation Priority

Build in this order:

### P0

```text
Next.js
FastAPI
PostgreSQL
PDF upload
Document parsing
RAG chat
```

### P1

```text
Concept extraction
Knowledge graph data model
Concept pages
News ingestion
News → CACS matching
```

### P2

```text
Practice engine
Mastery tracking
Personalized review
Daily brief
```

### P3

```text
Visual knowledge map
Advanced analytics
MCP exposure
Additional news providers
```

---

# 25. Definition of Done

The MVP is successful when the following complete flow works:

```text
1. User uploads CACS PDF
        ↓
2. System parses and indexes material
        ↓
3. System extracts CACS concepts
        ↓
4. Concepts are connected in graph
        ↓
5. Daily news is ingested automatically
        ↓
6. News is matched to CACS concepts
        ↓
7. User sees why the news relates to CACS
        ↓
8. User answers an application question
        ↓
9. Mastery estimate updates
        ↓
10. System recommends the next review
```

The architecture should make each stage replaceable without rewriting the entire application.