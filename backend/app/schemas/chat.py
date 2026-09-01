from pydantic import BaseModel, Field
from uuid import UUID


class ChatMessage(BaseModel):
    message: str = Field(..., description="User's question")


class SourceReference(BaseModel):
    document_title: str
    page_number: int
    content: str


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceReference] = []
