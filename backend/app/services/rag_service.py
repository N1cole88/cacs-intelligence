from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import get_settings
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.chat import ChatResponse, SourceReference

settings = get_settings()


class RAGService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.chat_model = settings.chat_model

    async def retrieve_relevant_chunks(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 5
    ) -> list[DocumentChunk]:
        """Retrieve relevant document chunks using semantic search."""
        # Generate query embedding
        embed_response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=query,
        )
        query_embedding = embed_response.data[0].embedding

        # Search using pgvector - cosine similarity
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def generate_response(
        self,
        query: str,
        retrieved_chunks: list[DocumentChunk],
    ) -> str:
        """Generate response using RAG pattern."""
        # Build context from retrieved chunks
        context_parts = []
        for chunk in retrieved_chunks:
            doc_title = chunk.document.title if chunk.document else "Unknown"
            context_parts.append(
                f"[Document: {doc_title}, Page {chunk.page_number}]\n{chunk.content}"
            )

        context = "\n\n---\n\n".join(context_parts)

        # Load system prompt
        import os
        prompt_dir = os.path.dirname(__file__).replace("\\", "/").replace("/services", "/prompts")
        system_prompt_path = os.path.join(prompt_dir, "rag_system.txt")
        with open(system_prompt_path, "r") as f:
            system_prompt = f.read()

        # Generate response
        response = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    async def chat(self, db: AsyncSession, message: str) -> ChatResponse:
        """Full RAG pipeline: retrieve + generate."""
        # Retrieve relevant chunks
        chunks = await self.retrieve_relevant_chunks(db, message)

        if not chunks:
            return ChatResponse(
                response="No relevant information found in your documents. Please upload some CACS study materials first.",
                sources=[],
            )

        # Generate response
        response_text = await self.generate_response(message, chunks)

        # Build sources
        sources = []
        seen_docs = set()
        for chunk in chunks:
            doc_title = chunk.document.title if chunk.document else "Unknown"
            if doc_title not in seen_docs:
                sources.append(
                    SourceReference(
                        document_title=doc_title,
                        page_number=chunk.page_number,
                        content=chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content,
                    )
                )
                seen_docs.add(doc_title)

        return ChatResponse(response=response_text, sources=sources)


def get_rag_service() -> RAGService:
    return RAGService()
