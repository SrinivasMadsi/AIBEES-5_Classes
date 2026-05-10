from functools import lru_cache
from langchain_google_vertexai import ChatVertexAI
from config import GCP_PROJECT_ID, GCP_LOCATION, LLM_MODEL, LLM_TEMPERATURE


@lru_cache(maxsize=1)
def get_llm():
    if not GCP_PROJECT_ID:
        raise EnvironmentError("GCP_PROJECT_ID not set in .env")
    return ChatVertexAI(
        model=LLM_MODEL,
        project=GCP_PROJECT_ID,
        location=GCP_LOCATION,
        temperature=LLM_TEMPERATURE,
    )
