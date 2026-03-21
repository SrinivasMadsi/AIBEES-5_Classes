"""
medical_app/main.py
────────────────────
FastAPI entry point.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from pydantic import BaseModel

from .config import settings
from .rag_service import _build_rag_chain, ask_question

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm the RAG chain on startup so first request is fast."""
    log.info("Pre-warming RAG chain...")
    try:
        _build_rag_chain()
        log.info("RAG chain ready ✓")
    except Exception as e:
        log.error("RAG chain failed to initialise: %s", e)
    yield
    log.info("Shutting down.")


app = FastAPI(
    title="Medical RAG API",
    version="1.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    query: str


@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_ID, "region": settings.REGION}


@app.post("/ask")
def ask(request: AskRequest):
    try:
        answer = ask_question(request.query)
        return {"answer": answer}
    except Exception as e:
        log.error("Error during /ask: %s", e)
        return {"error": str(e)}
