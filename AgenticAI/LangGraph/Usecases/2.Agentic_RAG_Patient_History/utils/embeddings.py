from functools import lru_cache
from langchain_google_vertexai import VertexAIEmbeddings
from config import GCP_PROJECT_ID, EMBEDDING_MODEL, GCP_LOCATION

@lru_cache(maxsize=1)
def get_embeddings():
    if not GCP_PROJECT_ID:
        raise EnvironmentError("GCP_PROJECT_ID not set in .env")
    return VertexAIEmbeddings(
        model_name=EMBEDDING_MODEL,
        project=GCP_PROJECT_ID,
        location=GCP_LOCATION
    )
