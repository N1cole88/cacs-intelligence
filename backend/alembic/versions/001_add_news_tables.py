"""add news tables

Revision ID: add_news_tables
Revises:
Create Date: 2026-09-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_news_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create news_articles table
    op.create_table(
        'news_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(1000), nullable=True),
        sa.Column('url', sa.String(2000), nullable=False, unique=True),
        sa.Column('image_url', sa.String(2000), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('source_name', sa.String(200), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('topics', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('relevance_score', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create news_matches table
    op.create_table(
        'news_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('news_article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('news_articles.id'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=True),
        sa.Column('concept', sa.String(500), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('news_matches')
    op.drop_table('news_articles')
