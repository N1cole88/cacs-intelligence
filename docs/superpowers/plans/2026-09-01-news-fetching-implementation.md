# News Fetching Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement news fetching from NewsAPI, GNews, and RSS with three toggleable views (Timeline, Relevance, Category) in the frontend.

**Architecture:** Backend fetches from 3 sources, stores in PostgreSQL, serves via REST API. Frontend displays with toggleable views. Celery handles scheduled fetching.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Celery, Next.js, Tailwind CSS

---

## File Structure

### Backend - New Files
```
backend/app/
├── models/
│   └── news.py              # NewsArticle, NewsMatch models
├── schemas/
│   └── news.py              # Pydantic schemas
├── services/
│   └── news_service.py      # News fetching & processing
└── api/routes/
    └── news.py              # API endpoints
```

### Backend - Modified Files
```
backend/app/
├── config.py                # Add news API keys
├── main.py                 # Add news router
└── workers/
    └── celery_app.py       # Add news scheduler
```

### Frontend - New Files
```
frontend/src/
├── app/news/
│   └── page.tsx            # News dashboard
├── components/
│   ├── NewsCard.tsx       # News article card
│   └── NewsFilters.tsx    # Filter controls
└── lib/
    └── news-api.ts        # News API client
```

---

## Tasks

### Task 1: Database Models

**Files:**
- Create: `backend/app/models/news.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create news models**

```python
# backend/app/models/news.py
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(String(1000), nullable=True)
    url: Mapped[str] = mapped_column(String(2000), unique=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # newsapi, gnews, rss
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    matches: Mapped[list["NewsMatch"]] = relationship(
        "NewsMatch",
        back_populates="article",
        cascade="all, delete-orphan",
    )


class NewsMatch(Base):
    __tablename__ = "news_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_article_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("news_articles.id"), nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    concept: Mapped[str] = mapped_column(String(500), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)

    article: Mapped["NewsArticle"] = relationship("NewsArticle", back_populates="matches")
```

- [ ] **Step 2: Update models __init__**

```python
# backend/app/models/__init__.py
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.news import NewsArticle, NewsMatch

__all__ = ["Document", "DocumentChunk", "NewsArticle", "NewsMatch"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/news.py backend/app/models/__init__.py
git commit -m "feat: add NewsArticle and NewsMatch models"
```

---

### Task 2: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/news.py`

- [ ] **Step 1: Create news schemas**

```python
# backend/app/schemas/news.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class NewsArticleBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    url: str
    image_url: Optional[str] = None
    source: str
    source_name: str
    published_at: datetime
    topics: list[str] = []
    relevance_score: float = 0.0


class NewsArticleResponse(NewsArticleBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class NewsMatchResponse(BaseModel):
    id: UUID
    document_id: Optional[UUID]
    concept: str
    match_score: float

    class Config:
        from_attributes = True


class NewsDetailResponse(NewsArticleBase):
    id: UUID
    created_at: datetime
    matches: list[NewsMatchResponse] = []

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    articles: list[NewsArticleResponse]
    total: int


class NewsRefreshResponse(BaseModel):
    message: str
    articles_fetched: int


class NewsSourceResponse(BaseModel):
    source: str
    name: str
    count: int
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/news.py
git commit -m "feat: add news Pydantic schemas"
```

---

### Task 3: News Service

**Files:**
- Create: `backend/app/services/news_service.py`

- [ ] **Step 1: Create news service with fetching logic**

```python
# backend/app/services/news_service.py
import httpx
import feedparser
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models.news import NewsArticle, NewsMatch
from app.models.document import Document
from app.models.chunk import DocumentChunk

settings = get_settings()

# AML topics for filtering
AML_TOPICS = [
    "Anti-Money Laundering",
    "Know Your Customer",
    "Combating Terrorist Financing",
    "Financial Crimes",
    "Sanctions",
    "Crypto/FinTech Regulation",
    "FATF Guidelines",
    "Bank Secrecy Act",
]

# Keywords per topic for classification
TOPIC_KEYWORDS = {
    "Anti-Money Laundering": ["aml", "anti-money laundering", "money laundering", "money laundering prevention"],
    "Know Your Customer": ["kyc", "know your customer", "customer due diligence", "cdd"],
    "Combating Terrorist Financing": ["ctf", "terrorist financing", "counter terrorist financing", "terrorist"],
    "Financial Crimes": ["financial crime", "fraud", "financial fraud", "white collar crime"],
    "Sanctions": ["sanctions", "ofac", "embargo", "economic sanctions"],
    "Crypto/FinTech Regulation": ["cryptocurrency", "bitcoin", "crypto", "fintech", "digital currency", "virtual asset"],
    "FATF Guidelines": ["fatf", "financial action task force", "fatf recommendations", "mutual evaluation"],
    "Bank Secrecy Act": ["bsa", "bank secrecy act", "currency transaction report", "suspicious activity"],
}

RSS_SOURCES = [
    {"name": "FATF News", "url": "https://www.fatf-gafi.org/rss/rss.xml"},
    {"name": "FinCEN News", "url": "https://www.fincen.gov/news/rss.xml"},
]


class NewsService:
    def __init__(self):
        self.newsapi_key = settings.newsapi_api_key
        self.gnews_key = settings.gnews_api_key

    def _classify_topics(self, title: str, content: str) -> list[str]:
        """Classify article by topics using keyword matching."""
        text = f"{title} {content}".lower()
        topics = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)
        return topics if topics else ["Other"]

    async def fetch_newsapi(self, query: str = "money laundering OR AML OR KYC") -> list[dict]:
        """Fetch from NewsAPI."""
        if not self.newsapi_key:
            return []
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": self.newsapi_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, timeout=10.0)
                data = resp.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "title": item.get("title", ""),
                        "content": item.get("description", "") or item.get("content", ""),
                        "summary": item.get("description", "")[:500],
                        "url": item.get("url", ""),
                        "image_url": item.get("urlToImage"),
                        "source": "newsapi",
                        "source_name": item.get("source", {}).get("name", "NewsAPI"),
                        "published_at": item.get("publishedAt", ""),
                    })
                return articles
            except Exception:
                return []

    async def fetch_gnews(self, query: str = "anti-money laundering OR AML OR KYC") -> list[dict]:
        """Fetch from GNews API."""
        if not self.gnews_key:
            return []
        url = f"https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "max": 20,
            "apikey": self.gnews_key,
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, timeout=10.0)
                data = resp.json()
                articles = []
                for item in data.get("articles", []):
                    articles.append({
                        "title": item.get("title", ""),
                        "content": item.get("description", "") or item.get("content", ""),
                        "summary": item.get("description", "")[:500],
                        "url": item.get("url", ""),
                        "image_url": item.get("image"),
                        "source": "gnews",
                        "source_name": item.get("source", {}).get("name", "GNews"),
                        "published_at": item.get("publishedAt", ""),
                    })
                return articles
            except Exception:
                return []

    def fetch_rss(self) -> list[dict]:
        """Fetch from RSS feeds."""
        articles = []
        for rss in RSS_SOURCES:
            try:
                feed = feedparser.parse(rss["url"])
                for entry in feed.entries[:10]:
                    published = entry.get("published", datetime.utcnow().isoformat())
                    articles.append({
                        "title": entry.get("title", ""),
                        "content": entry.get("summary", ""),
                        "summary": entry.get("summary", "")[:500] if entry.get("summary") else "",
                        "url": entry.get("link", ""),
                        "image_url": None,
                        "source": "rss",
                        "source_name": rss["name"],
                        "published_at": published,
                    })
            except Exception:
                continue
        return articles

    async def fetch_all_news(self) -> list[dict]:
        """Fetch from all sources."""
        # Fetch from APIs
        newsapi_articles = await self.fetch_newsapi()
        gnews_articles = await self.fetch_gnews()
        rss_articles = self.fetch_rss()

        # Combine and deduplicate
        all_articles = newsapi_articles + gnews_articles + rss_articles
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        return unique_articles

    async def save_articles(self, db: AsyncSession, articles: list[dict]) -> int:
        """Save articles to database, return count."""
        count = 0
        for article in articles:
            # Check if exists
            stmt = select(NewsArticle).where(NewsArticle.url == article["url"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                continue

            # Parse date
            try:
                published_at = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
            except:
                published_at = datetime.utcnow()

            # Classify topics
            topics = self._classify_topics(article["title"], article["content"])

            db_article = NewsArticle(
                title=article["title"],
                content=article["content"][:5000],
                summary=article.get("summary"),
                url=article["url"],
                image_url=article.get("image_url"),
                source=article["source"],
                source_name=article["source_name"],
                published_at=published_at,
                topics=topics,
            )
            db.add(db_article)
            count += 1

        await db.commit()
        return count

    async def get_articles(
        self,
        db: AsyncSession,
        source: str | None = None,
        topic: str | None = None,
        view: str = "timeline",
        limit: int = 50,
    ) -> tuple[list[NewsArticle], int]:
        """Get articles with filters."""
        stmt = select(NewsArticle)

        if source and source != "all":
            stmt = stmt.where(NewsArticle.source == source)
        if topic and topic != "all":
            stmt = stmt.where(NewsArticle.topics.contains([topic]))

        # Get total count
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Order by
        if view == "relevance":
            stmt = stmt.order_by(NewsArticle.relevance_score.desc())
        else:  # timeline or category
            stmt = stmt.order_by(NewsArticle.published_at.desc())

        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        articles = result.scalars().all()

        return list(articles), total


def get_news_service() -> NewsService:
    return NewsService()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/news_service.py
git commit -m "feat: add news service with multi-source fetching"
```

---

### Task 4: News API Routes

**Files:**
- Create: `backend/app/api/routes/news.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create news routes**

```python
# backend/app/api/routes/news.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.news import (
    NewsListResponse,
    NewsArticleResponse,
    NewsDetailResponse,
    NewsRefreshResponse,
    NewsSourceResponse,
)
from app.services.news_service import get_news_service, NewsService

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=NewsListResponse)
async def get_news(
    source: str | None = Query(None, description="Filter by source: newsapi, gnews, rss"),
    topic: str | None = Query(None, description="Filter by topic"),
    view: str = Query("timeline", description="View mode: timeline, relevance, category"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    service: NewsService = Depends(get_news_service),
):
    articles, total = await service.get_articles(db, source, topic, view, limit)
    return NewsListResponse(
        articles=[NewsArticleResponse.model_validate(a) for a in articles],
        total=total,
    )


@router.get("/{article_id}", response_model=NewsDetailResponse)
async def get_news_detail(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    service: NewsService = Depends(get_news_service),
):
    from uuid import UUID
    from sqlalchemy import select
    from app.models.news import NewsArticle

    stmt = select(NewsArticle).where(NewsArticle.id == UUID(article_id))
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Article not found")
    return NewsDetailResponse.model_validate(article)


@router.post("/refresh", response_model=NewsRefreshResponse)
async def refresh_news(
    db: AsyncSession = Depends(get_db),
    service: NewsService = Depends(get_news_service),
):
    articles = await service.fetch_all_news()
    count = await service.save_articles(db, articles)
    return NewsRefreshResponse(
        message="News refreshed successfully",
        articles_fetched=count,
    )


@router.get("/sources/list", response_model=list[NewsSourceResponse])
async def get_sources(
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.models.news import NewsArticle

    stmt = (
        select(NewsArticle.source, NewsArticle.source_name, func.count().label("count"))
        .group_by(NewsArticle.source, NewsArticle.source_name)
    )
    result = await db.execute(stmt)
    return [
        NewsSourceResponse(source=row[0], name=row[1], count=row[2])
        for row in result.all()
    ]
```

- [ ] **Step 2: Update main.py to include news router**

```python
# backend/app/main.py - add news to imports and router
from app.api.routes import documents, chat, news

# ... existing code ...
app.include_router(news.router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/routes/news.py backend/app/main.py
git commit -m "feat: add news API routes"
```

---

### Task 5: Config - Add News API Keys

**Files:**
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add news API keys to config**

```python
# backend/app/config.py - add these fields
# News API
newsapi_api_key: str = ""
gnews_api_key: str = ""
```

- [ ] **Step 2: Update docker-compose.yml with keys**

```yaml
# docker-compose.yml - add to backend environment
NEWSAPI_API_KEY: 831acdcef7c2480f88a9190e3adc4caa
GNEWS_API_KEY: 0fa5df874e0880b8f54d3c2e99029bbc
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/config.py docker-compose.yml
git commit -m "feat: add news API keys to config"
```

---

### Task 6: Database Migration

**Files:**
- Create: Alembic migration

- [ ] **Step 1: Create migration**

Run: `cd backend && alembic revision --autogenerate -m "add news tables"`

Expected: Creates migration file in alembic/versions/

- [ ] **Step 2: Run migration**

Run: `cd backend && alembic upgrade head`

Expected: Creates news_articles and news_matches tables

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: add news tables migration"
```

---

### Task 7: Frontend - News API Client

**Files:**
- Create: `frontend/src/lib/news-api.ts`

- [ ] **Step 1: Create news API client**

```typescript
// frontend/src/lib/news-api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface NewsArticle {
  id: string;
  title: string;
  content: string;
  summary: string | null;
  url: string;
  image_url: string | null;
  source: string;
  source_name: string;
  published_at: string;
  topics: string[];
  relevance_score: number;
  created_at: string;
}

export interface NewsListResponse {
  articles: NewsArticle[];
  total: number;
}

export interface NewsSource {
  source: string;
  name: string;
  count: number;
}

export async function fetchNews(params: {
  source?: string;
  topic?: string;
  view?: string;
  limit?: number;
}): Promise<NewsListResponse> {
  const searchParams = new URLSearchParams();
  if (params.source) searchParams.set("source", params.source);
  if (params.topic) searchParams.set("topic", params.topic);
  if (params.view) searchParams.set("view", params.view);
  if (params.limit) searchParams.set("limit", params.limit.toString());

  const res = await fetch(`${API_URL}/api/news?${searchParams}`);
  if (!res.ok) throw new Error("Failed to fetch news");
  return res.json();
}

export async function refreshNews(): Promise<{ articles_fetched: number }> {
  const res = await fetch(`${API_URL}/api/news/refresh`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to refresh news");
  return res.json();
}

export async function getNewsSources(): Promise<NewsSource[]> {
  const res = await fetch(`${API_URL}/api/news/sources/list`);
  if (!res.ok) throw new Error("Failed to fetch sources");
  return res.json();
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/news-api.ts
git commit -m "feat: add news API client"
```

---

### Task 8: Frontend - News Card Component

**Files:**
- Create: `frontend/src/components/NewsCard.tsx`

- [ ] **Step 1: Create NewsCard component**

```typescript
// frontend/src/components/NewsCard.tsx
import { NewsArticle } from "@/lib/news-api";
import { ExternalLink, Clock, Newspaper } from "lucide-react";

interface NewsCardProps {
  article: NewsArticle;
  showRelevance?: boolean;
}

export function NewsCard({ article, showRelevance = false }: NewsCardProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-lg line-clamp-2">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-600"
          >
            {article.title}
          </a>
        </h3>
        {showRelevance && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            {Math.round(article.relevance_score * 100)}% match
          </span>
        )}
      </div>

      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
        <span className="flex items-center gap-1">
          <Newspaper className="w-4 h-4" />
          {article.source_name}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          {formatDate(article.published_at)}
        </span>
      </div>

      {article.summary && (
        <p className="mt-3 text-gray-600 line-clamp-3">{article.summary}</p>
      )}

      {article.topics.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {article.topics.map((topic) => (
            <span
              key={topic}
              className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
            >
              {topic}
            </span>
          ))}
        </div>
      )}

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        Read More <ExternalLink className="w-4 h-4" />
      </a>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/NewsCard.tsx
git commit -m "feat: add NewsCard component"
```

---

### Task 9: Frontend - News Page

**Files:**
- Create: `frontend/src/app/news/page.tsx`
- Modify: `frontend/src/app/page.tsx` (add News link)

- [ ] **Step 1: Create News page**

```typescript
// frontend/src/app/news/page.tsx
"use client";
import { useState, useEffect } from "react";
import { fetchNews, refreshNews, NewsArticle } from "@/lib/news-api";
import { NewsCard } from "@/components/NewsCard";
import { RefreshCw, Filter, LayoutGrid, List, BarChart3 } from "lucide-react";

const TOPICS = [
  "All",
  "Anti-Money Laundering",
  "Know Your Customer",
  "Combating Terrorist Financing",
  "Financial Crimes",
  "Sanctions",
  "Crypto/FinTech Regulation",
  "FATF Guidelines",
  "Bank Secrecy Act",
];

const SOURCES = ["all", "newsapi", "gnews", "rss"];
const VIEWS = [
  { id: "timeline", label: "Timeline", icon: List },
  { id: "relevance", label: "Relevance", icon: BarChart3 },
  { id: "category", label: "Category", icon: LayoutGrid },
];

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  // Filters
  const [view, setView] = useState("timeline");
  const [source, setSource] = useState("all");
  const [topic, setTopic] = useState("All");

  const loadNews = async () => {
    setLoading(true);
    try {
      const params: any = { view };
      if (source !== "all") params.source = source;
      if (topic !== "All") params.topic = topic;
      const data = await fetchNews(params);
      setArticles(data.articles);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      console.error("Failed to load news:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshNews();
      await loadNews();
    } catch (err) {
      console.error("Failed to refresh news:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadNews();
  }, [view, source, topic]);

  // Group by category for category view
  const groupedArticles = view === "category"
    ? articles.reduce((acc, article) => {
        article.topics.forEach((t) => {
          if (!acc[t]) acc[t] = [];
          acc[t].push(article);
        });
        return acc;
      }, {} as Record<string, NewsArticle[]>)
    : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Financial News</h1>
            {lastUpdated && (
              <p className="text-sm text-gray-500">Last updated: {lastUpdated}</p>
            )}
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-4">
        {/* Filters */}
        <div className="bg-white rounded-lg border p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* View Toggle */}
            <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg">
              {VIEWS.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setView(v.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${
                    view === v.id
                      ? "bg-white shadow text-gray-900"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                >
                  <v.icon className="w-4 h-4" />
                  {v.label}
                </button>
              ))}
            </div>

            {/* Source Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="border rounded-md px-3 py-1.5 text-sm"
              >
                {SOURCES.map((s) => (
                  <option key={s} value={s}>
                    {s === "all" ? "All Sources" : s.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            {/* Topic Filter */}
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="border rounded-md px-3 py-1.5 text-sm"
            >
              {TOPICS.map((t) => (
                <option key={t} value={t}>
                  {t === "All" ? "All Topics" : t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* News Content */}
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-gray-400 mx-auto" />
            <p className="mt-2 text-gray-500">Loading news...</p>
          </div>
        ) : view === "category" && groupedArticles ? (
          /* Category View */
          <div className="space-y-8">
            {Object.entries(groupedArticles).map(([category, cats]) => (
              <div key={category}>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  {category}
                  <span className="text-sm bg-gray-200 px-2 py-0.5 rounded-full">
                    {cats.length}
                  </span>
                </h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {cats.slice(0, 6).map((article) => (
                    <NewsCard key={article.id} article={article} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Timeline / Relevance View */
          <div className="grid md:grid-cols-2 gap-4">
            {articles.map((article) => (
              <NewsCard
                key={article.id}
                article={article}
                showRelevance={view === "relevance"}
              />
            ))}
          </div>
        )}

        {!loading && articles.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No news articles found. Try adjusting your filters or refresh.
          </div>
        )}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Add News link to homepage**

```typescript
// frontend/src/app/page.tsx - add News card
<a href="/news" className="p-6 bg-white rounded-lg border hover:shadow-md transition-shadow">
  <Newspaper className="h-10 w-10 text-red-600 mb-4" />
  <h3 className="text-lg font-semibold">News</h3>
  <p className="text-sm text-gray-600 mt-1">Latest AML/CACS news</p>
</a>
```

- [ ] **Step 3: Add Newspaper import to page.tsx**

```typescript
import { FileText, MessageSquare, BarChart3, BookOpen, Newspaper } from "lucide-react";
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/news/page.tsx frontend/src/app/page.tsx
git commit -m "feat: add news dashboard page with three views"
```

---

### Task 10: Test End-to-End

- [ ] **Step 1: Start the services**

```bash
docker-compose up -d
```

- [ ] **Step 2: Test API endpoints**

```bash
# Health check
curl http://localhost:8000/health

# Fetch news
curl http://localhost:8000/api/news

# Refresh news
curl -X POST http://localhost:8000/api/news/refresh
```

Expected: Returns news articles

- [ ] **Step 3: Test frontend**

Open: http://localhost:3000/news

Expected: News dashboard loads with three view toggles

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: complete news fetching feature"
```

---

## Summary

Total: 10 tasks

- Database models (Task 1)
- Pydantic schemas (Task 2)
- News service (Task 3)
- API routes (Task 4)
- Config with API keys (Task 5)
- Database migration (Task 6)
- Frontend API client (Task 7)
- NewsCard component (Task 8)
- News page with 3 views (Task 9)
- E2E testing (Task 10)
