"""
main.py
FastAPI entry point for AI_Onboarding_Platform backend.

Run with:
  poetry run uvicorn main:app --reload --port 8000
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Avoid OpenMP duplicate lib issues on some systems

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import data_router, review_router, submissions_router, validate_router
from core.db import healthcheck

app = FastAPI(
    title="AI_Onboarding_Platform API",
    description="Multi-agent client configuration validation with MCP, HITL, and Langfuse",
    version="0.1.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(submissions_router)
app.include_router(validate_router)
app.include_router(review_router)
app.include_router(data_router)


@app.get("/")
def root():
    return {
        "service": "AI_Onboarding_Platform",
        "status":  "running",
        "docs":    "/docs",
    }


@app.get("/health")
def health():
    return {
        "api": "ok",
        "database": "ok" if healthcheck() else "unreachable",
    }
