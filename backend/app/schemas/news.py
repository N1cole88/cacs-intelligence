from pydantic import BaseModel
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
