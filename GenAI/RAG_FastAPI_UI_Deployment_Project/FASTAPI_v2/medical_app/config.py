"""
medical_app/config.py
──────────────────────
Pydantic settings — reads from environment variables or .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    PROJECT_ID:  str
    REGION:      str
    INDEX_ID:    str
    ENDPOINT_ID: str
    BUCKET:      str
    EMBED_MODEL: str
    CHAT_MODEL:  str

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Single instance for direct imports
settings = get_settings()
