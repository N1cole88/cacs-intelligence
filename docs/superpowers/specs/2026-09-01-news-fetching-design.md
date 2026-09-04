# News Fetching Feature Design

## Overview

Fetch AML/CACS news from multiple sources, match against user's uploaded documents, and display in a toggleable news dashboard.

---

## News Sources

| Source | API Key Required | Implementation |
|--------|------------------|----------------|
| NewsAPI.org | `831acdcef7c2480f88a9190e3adc4caa` | REST API |
| GNews API | `0fa5df874e0880b8f54d3c2e99029bbc` | REST API |
| RSS Feeds | No | XML parsing |

### RSS Sources
- FATF News: https://www.fatf-gafi.org/rss/rss.xml
- FinCEN News: https://www.fincen.gov/news/rss.xml
- U.S. Treasury Sanctions: https://home.treasury.gov/about/policy-offices/office-of-financial-research/rss-feed
- ACAMS Today: https://www.acams.org/en/feed
- AML Right Source: https://www.amlrightsource.com/news/feed

---

## Topics Filtered

1. Anti-Money Laundering (AML)
2. Know Your Customer (KYC)
3. Combating Terrorist Financing (CTF)
4. Financial Crimes
5. Sanctions
6. Crypto/FinTech Regulation
7. FATF Guidelines
8. Bank Secrecy Act (BSA)

---

## Backend Architecture

### New Files

```
backend/app/
├── models/
│   └── news.py              # NewsArticle, NewsMatch models
├── schemas/
│   └── news.py              # Pydantic schemas for news
├── services/
│   └── news_service.py      # News fetching & processing
├── workers/
│   └── news_scheduler.py    # Celery tasks for auto-refresh
└── api/routes/
    └── news.py              # API endpoints
```

### Database Schema

**NewsArticle**
- id: UUID
- title: str
- content: str (truncated)
- summary: str
- url: str
- image_url: str (nullable)
- source: str (newsapi/gnews/rss)
- source_name: str
- published_at: datetime
- topics: list[str] (JSON)
- relevance_score: float (0-1)
- created_at: datetime

**NewsMatch**
- id: UUID
- news_article_id: FK
- document_id: FK (nullable)
- concept: str (matched concept from document)
- match_score: float

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/news | Fetch news (filters: source, topic, date, view) |
| POST | /api/news/refresh | Manual refresh trigger |
| GET | /api/news/sources | List available sources |
| GET | /api/news/{id} | Get single article details |

---

## Frontend Architecture

### New Page
`/news` - News Dashboard

### UI Components

1. **Header Bar**
   - Title: "Financial News"
   - "Refresh" button (manual fetch)
   - Last updated timestamp

2. **View Toggle**
   - Three tabs: Timeline | Relevance | Category

3. **Filters (above cards)**
   - Source dropdown: All | NewsAPI | GNews | RSS
   - Topic dropdown: All | AML | KYC | CTF | etc.
   - Date range: Today | This Week | This Month | All

4. **News Cards**
   - Headline (clickable to expand)
   - Source badge + publication date
   - Summary (2-3 lines)
   - Matched topics (tags)
   - Relevance score (if relevance view)
   - "Read More" external link

### View Modes

1. **Timeline View**
   - Sorted by published_at (newest first)
   - Simple vertical list

2. **Relevance View**
   - Sorted by relevance_score (highest first)
   - Show "Matched to: [document name]" on cards

3. **Category View**
   - Grouped by topic
   - Collapsible sections per topic
   - Count badge per category

---

## Data Flow

1. **Fetch Phase**
   - Parallel fetch from NewsAPI, GNews, RSS
   - Deduplicate by URL
   - Classify topics using keyword matching

2. **Match Phase**
   - Compare against user's uploaded documents
   - Use existing RAG embeddings for similarity
   - Score relevance 0-1

3. **Storage Phase**
   - Store in NewsArticle table
   - Create NewsMatch records for document links

4. **Display Phase**
   - Serve via API with filters
   - Frontend renders based on selected view

---

## Auto-Refresh Schedule

- **Daily job** (default): Runs at midnight local time
- **On-demand**: User clicks refresh button
- Implemented via Celery beat schedule

---

## Configuration

```python
# Environment variables
NEWSAPI_API_KEY=831acdcef7c2480f88a9190e3adc4caa
GNEWS_API_KEY=0fa5df874e0880b8f54d3c2e99029bbc
NEWS_FETCH_INTERVAL_HOURS=24
```

---

## Acceptance Criteria

1. ✅ News fetches from all 3 sources (NewsAPI, GNews, RSS)
2. ✅ Articles filtered by 8 AML topics
3. ✅ Three toggleable views: Timeline, Relevance, Category
4. ✅ Manual refresh button works
5. ✅ Daily auto-refresh scheduled
6. ✅ News cards show: headline, source, date, summary, topics
7. ✅ Filter by source and topic works
8. ✅ Relevance view shows matched documents
