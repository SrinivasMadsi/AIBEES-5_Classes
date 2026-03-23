"""
Application Configuration
All settings are driven by environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ------------------------------------------------------------------
    # Runtime mode
    # ------------------------------------------------------------------
    # If USE_VERTEXAI=1, the app uses Vertex AI (Gemini) for embeddings + generation.
    # If USE_VERTEXAI=0 (default), it runs locally using a simple keyword retriever
    # and does NOT require any cloud credentials. This is ideal for classroom demos.
    USE_VERTEXAI: bool = os.getenv("USE_VERTEXAI", "0").strip() in {"1", "true", "True"}

    # ------------------------------------------------------------------
    # GCP / Vertex AI (only required when USE_VERTEXAI=1)
    # ------------------------------------------------------------------
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")

    # ------------------------------------------------------------------
    # Model Settings
    # ------------------------------------------------------------------
    # Note: Vertex embedding model names change over time; keep overridable via env.
    # (Google docs mention "gemini-embedding-001" as a current option.)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-005")

    # Allow either GEMINI_MODEL (common) or LLM_MODEL to drive the model id.
    LLM_MODEL: str = os.getenv("GEMINI_MODEL", os.getenv("LLM_MODEL", "gemini-2.5-pro"))

    # Lower temperature → more deterministic factual answers (better for RAG)
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))
    TOP_K: int = 40
    TOP_P: float = 0.8

    # ------------------------------------------------------------------
    # Document Processing
    # ------------------------------------------------------------------
    PDF_PATH: str = os.getenv("PDF_PATH", "customer_credit_data_100_records.pdf")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    # Number of chunks to retrieve per query
    RETRIEVER_TOP_K: int = int(os.getenv("RETRIEVER_TOP_K", "4"))

    # ------------------------------------------------------------------
    # Index
    # ------------------------------------------------------------------
    FAISS_INDEX_DIR: str = os.getenv("FAISS_INDEX_DIR", "faiss_index")

    # ------------------------------------------------------------------
    # Validation helper
    # ------------------------------------------------------------------
    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of missing required config keys."""
        missing = []
        if cls.USE_VERTEXAI:
            if not cls.GCP_PROJECT_ID:
                missing.append("GCP_PROJECT_ID")
            if not cls.GCP_REGION:
                missing.append("GCP_REGION")
        return missing
