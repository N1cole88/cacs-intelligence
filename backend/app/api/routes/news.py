from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
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
):
    from app.models.news import NewsArticle

    try:
        uuid_id = UUID(article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID")

    stmt = select(NewsArticle).where(NewsArticle.id == uuid_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return NewsDetailResponse.model_validate(article)


@router.post("/refresh", response_model=NewsRefreshResponse)
async def refresh_news(
    db: AsyncSession = Depends(get_db),
    service: NewsService = Depends(get_news_service),
):
    articles = await service.fetch_all_news()
    count = await service.save_articles(db, articles)
    # Also update relevance scores based on user's documents
    await service.update_relevance_scores(db)
    return NewsRefreshResponse(
        message="News refreshed successfully",
        articles_fetched=count,
    )


@router.post("/calculate-relevance")
async def calculate_relevance(
    db: AsyncSession = Depends(get_db),
    service: NewsService = Depends(get_news_service),
):
    """Calculate relevance scores based on user's uploaded documents."""
    count = await service.update_relevance_scores(db)
    return {"message": "Relevance scores updated", "articles_updated": count}


@router.get("/sources/list", response_model=list[NewsSourceResponse])
async def get_sources(
    db: AsyncSession = Depends(get_db),
):
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
