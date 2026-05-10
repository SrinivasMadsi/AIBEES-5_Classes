"""
core/llm.py
ChatVertexAI factory. Authentication uses Application Default Credentials (ADC).
Run `gcloud auth application-default login` once before using.
"""
from functools import lru_cache

from langchain_google_vertexai import ChatVertexAI

from config.settings import settings


@lru_cache(maxsize=4)
def get_llm(temperature: float | None = None, model: str | None = None) -> ChatVertexAI:
    """
    Returns a cached ChatVertexAI instance.
    Pass `temperature` or `model` to override defaults from .env.
    """
    if not settings.gcp_project_id:
        raise EnvironmentError("GCP_PROJECT_ID not set in .env")

    return ChatVertexAI(
        model=model or settings.llm_model,
        project=settings.gcp_project_id,
        location=settings.gcp_location,
        temperature=temperature if temperature is not None else settings.llm_temperature,
    )
