"""
core/llm.py
LLM factory — single place to initialise the language model.

All agents and nodes import get_llm() from here.
Swapping models only needs a change here.

Authentication: Uses gcloud auth application-default login (Vertex AI).
No API key required — credentials come from the gcloud CLI.
"""

from langchain_google_vertexai import ChatVertexAI
from config.settings import settings


def get_llm(temperature: float = None) -> ChatVertexAI:
    """
    Returns a configured Vertex AI LLM instance.
    Uses application default credentials from: gcloud auth application-default login
    Temperature defaults to settings value if not provided.
    """
    return ChatVertexAI(
        model_name    = settings.vertex_model,
        project       = settings.gcp_project_id,
        location      = settings.gcp_region,
        temperature   = temperature if temperature is not None else settings.llm_temperature,
        max_output_tokens = 2048,
    )