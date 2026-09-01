import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
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
