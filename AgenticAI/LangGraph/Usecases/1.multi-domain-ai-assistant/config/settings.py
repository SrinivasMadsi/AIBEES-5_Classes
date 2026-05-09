"""
config/settings.py
Centralized configuration — loads .env and exposes typed settings.

All other modules import from here — never from os.getenv directly.
This means changing a config key only needs updating in ONE place.

Authentication method: Vertex AI via gcloud CLI
  Run once: gcloud auth application-default login
  No GOOGLE_API_KEY needed.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """
    Typed, immutable settings object.
    frozen=True means no accidental mutation at runtime.
    """

    # ── Vertex AI (gcloud auth) ───────────────────────────────
    # No API key needed — uses application default credentials
    # Run: gcloud auth application-default login
    gcp_project_id:  str = os.getenv("GCP_PROJECT_ID", "")
    gcp_region:      str = os.getenv("GCP_REGION", "us-central1")
    vertex_model:    str = os.getenv("VERTEX_MODEL", "gemini-2.5-pro")
    llm_temperature: float = 0.0

    # ── Vertex AI Embeddings ──────────────────────────────────
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")

    # ── Database ──────────────────────────────────────────────
    sqlite_db_path:  str = os.getenv("SQLITE_DB_PATH", "db/enterprise.db")

    # ── Vector Store ─────────────────────────────────────────
    vector_store_path: str = os.getenv("VECTOR_STORE_PATH", "vector_stores/")

    # ── Langfuse ──────────────────────────────────────────────
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host:       str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    langfuse_enabled:    bool = bool(os.getenv("LANGFUSE_PUBLIC_KEY", ""))

    # ── App ───────────────────────────────────────────────────
    session_id: str = os.getenv("SESSION_ID", "enterprise-ai-session")
    user_id:    str = os.getenv("USER_ID",    "demo-user")


# ── Singleton instance ────────────────────────────────────────────────────────
# Import this anywhere: from config.settings import settings
settings = Settings()