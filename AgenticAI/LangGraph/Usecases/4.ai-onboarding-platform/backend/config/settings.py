"""
config/settings.py
Centralized settings loaded from .env file at project root.
"""
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is 2 levels up from this file (backend/config/settings.py → project root)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from .env"""

    # ── Database ───────────────────────────────────────────────────────────
    business_db_url: str
    agent_db_url: str

    # ── Google Cloud / Vertex AI ──────────────────────────────────────────
    gcp_project_id: str
    gcp_location: str = "us-central1"
    llm_model: str = "gemini-2.5-pro"
    llm_temperature: float = 0.0

    # ── Langfuse (optional) ───────────────────────────────────────────────
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # ── MCP server ────────────────────────────────────────────────────────
    # Path to the sop-mcp server.py file (relative to project root)
    sop_mcp_server_path: str = "mcp-servers/sop-mcp/server.py"

    # ── Application ───────────────────────────────────────────────────────
    max_self_correction_iterations: int = 1
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
