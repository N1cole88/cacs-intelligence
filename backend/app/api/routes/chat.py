from functools import lru_cache
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@lru_cache()
def get_rag_service() -> RAGService:
    return RAGService()


@router.post("", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """RAG-powered chat endpoint."""
    rag_service = get_rag_service()
    return await rag_service.chat(db, message.message)
