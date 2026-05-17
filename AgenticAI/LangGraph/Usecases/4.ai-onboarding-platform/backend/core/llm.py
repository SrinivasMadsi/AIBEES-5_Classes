"""
core/llm.py
Factory for the Vertex AI Gemini LLM. Cached to avoid reinitialization.
"""
from functools import lru_cache

from langchain_google_vertexai import ChatVertexAI

from config.settings import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatVertexAI:
    """Return the singleton ChatVertexAI instance."""
    return ChatVertexAI(
        model=settings.llm_model,
        project=settings.gcp_project_id,
        location=settings.gcp_location,
        temperature=settings.llm_temperature,
        max_output_tokens=4096,
    )
