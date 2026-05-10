"""
config/settings.py
Centralized configuration loaded from environment variables.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root is two levels up from this file (backend/config/settings.py)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """All app settings, loaded from .env at the project root."""

    # ── Database ─────────────────────────────────────────────────────────────
    business_db_url: str
    agent_db_url: str

    # ── Vertex AI ────────────────────────────────────────────────────────────
    gcp_project_id: str
    gcp_location: str = "us-central1"
    llm_model: str = "gemini-2.5-pro"
    llm_temperature: float = 0.0

    # ── Langfuse ─────────────────────────────────────────────────────────────
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # ── App ──────────────────────────────────────────────────────────────────
    max_self_correction_iterations: int = 1
    default_region: str = "Telangana"
    default_warehouse: str = "Hyderabad-WH1"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
