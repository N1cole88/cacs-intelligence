from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(message: str):
    return {"response": "Chat endpoint - to be implemented"}
