"""
main.py
FastAPI entry point. Run with:
    uvicorn main:app --reload --port 8000
"""
import logging
import os

# Workaround for Windows OpenMP runtime conflict (FAISS + Vertex AI)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import routes_chat, routes_data
from config.settings import settings
from core.db import healthcheck

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Purchase Order Agent",
    description="Multi-agent system for converting NL requests into validated POs",
    version="0.1.0",
)

# CORS — allow the frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_chat.router)
app.include_router(routes_data.router)


@app.get("/health")
def health():
    """Liveness + DB readiness check."""
    return {
        "status": "ok",
        "db": "ok" if healthcheck() else "unreachable",
        "llm_model": settings.llm_model,
        "langfuse": settings.langfuse_enabled,
    }


@app.get("/")
def root():
    return {
        "service": "po-agent",
        "docs": "/docs",
        "health": "/health",
    }
