"""
medical_app/rag_service.py
──────────────────────────
RAG pipeline using Vertex AI Vector Search + Gemini via LangChain.
"""

from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_vertexai import ChatVertexAI, VectorSearchVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from .config import settings


@lru_cache(maxsize=1)
def _build_rag_chain():
    """
    Lazily build and cache the RAG chain on first request.
    Using lru_cache ensures we initialise only once per process.
    """

    # 1. Embeddings — GoogleGenerativeAIEmbeddings supports gemini-embedding-001
    embedding_model = GoogleGenerativeAIEmbeddings(
        model=settings.EMBED_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        task_type="RETRIEVAL_QUERY",
    )

    # 2. Vector store
    vector_store = VectorSearchVectorStore.from_components(
        project_id=settings.PROJECT_ID,
        region=settings.REGION,
        gcs_bucket_name=settings.BUCKET,
        index_id=settings.INDEX_ID,
        endpoint_id=settings.ENDPOINT_ID,
        embedding=embedding_model,
    )

    # 3. LLM
    llm = ChatVertexAI(
        model=settings.CHAT_MODEL,
        project=settings.PROJECT_ID,
        location=settings.REGION,
        temperature=0.2,
        max_tokens=1024,
    )

    # 4. Prompt
    prompt = ChatPromptTemplate.from_template("""
Answer the question in 3-4 sentences based only on the following context:
{context}

Question: {input}
""")

    # 5. Chains
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    return create_retrieval_chain(retriever, document_chain)


def ask_question(query: str) -> str:
    """Run the RAG pipeline for a given query."""
    rag_chain = _build_rag_chain()
    response = rag_chain.invoke({"input": query})
    return response["answer"]
