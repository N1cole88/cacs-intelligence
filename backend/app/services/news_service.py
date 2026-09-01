import httpx
import feedparser
from datetime import datetime
from sqlalchemy import select, func
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
        url = "https://gnews.io/api/v4/search"
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
