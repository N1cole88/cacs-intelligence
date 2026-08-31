from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize connections
    settings = get_settings()
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="CACS Intelligence API",
    description="Personal AI learning platform for CACS exam prep",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "CACS Intelligence API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
