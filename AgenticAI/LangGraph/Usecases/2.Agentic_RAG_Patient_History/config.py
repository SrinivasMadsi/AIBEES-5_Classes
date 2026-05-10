"""
config.py — single source of truth for all settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────
# Prefer Vertex AI configuration: set `GCP_PROJECT_ID` and optional `GCP_LOCATION`.
GCP_PROJECT_ID: str    = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION: str      = os.getenv("GCP_LOCATION", "us-central1")
# Use the Vertex model recommended by GCP
LLM_MODEL: str         = os.getenv("LLM_MODEL", "gemini-2.5-pro")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

# ── Embedding ──────────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "text-embedding-005"

# ── Langfuse ───────────────────────────────────────────────────────────────
LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST: str       = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# ── RAG settings ───────────────────────────────────────────────────────────
CHUNK_SIZE: int        = 800
CHUNK_OVERLAP: int     = 100
TOP_K: int             = 5
MAX_AGENT_ITERATIONS: int = 4   # agentic RAG loop safety guard

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_DIR: Path          = Path(__file__).parent / "data"
FAISS_DIR: Path         = DATA_DIR / "faiss_store"
COMBINED_INDEX: Path    = FAISS_DIR / "combined_index"
REGISTRY_FILE: Path     = FAISS_DIR / "registry.json"
SAMPLE_RECORDS: Path    = DATA_DIR / "sample_records"

# ── AIBees brand colours (used in app.py) ─────────────────────────────────
BRAND_ORANGE  = "#E8500A"
BRAND_DARK    = "#3A3A3A"
BRAND_YELLOW  = "#F5C518"
BRAND_LIGHT   = "#FFF8F3"
BRAND_ORANGE2 = "#FF6B2B"
