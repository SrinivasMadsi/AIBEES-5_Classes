"""
RAG Engine using Google Vertex AI Vector Search (Incremental)
"""
import os
import uuid
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine import MatchingEngineIndex, MatchingEngineIndexEndpoint

load_dotenv()

# ── Config ──────────────────────────────────────────────
PROJECT_ID          = os.getenv("GCP_PROJECT_ID")
REGION              = os.getenv("GCP_REGION", "us-central1")
INDEX_ID            = os.getenv("INDEX_ID")
INDEX_ENDPOINT_ID   = os.getenv("INDEX_ENDPOINT_ID")
DEPLOYED_INDEX_ID   = os.getenv("DEPLOYED_INDEX_ID")

# In-memory store: {doc_id: {"text": str, "metadata": dict}}
doc_store: dict[str, dict] = {}

# ── Init Vertex AI ───────────────────────────────────────
aiplatform.init(project=PROJECT_ID, location=REGION)

embedder = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
llm      = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def add_documents(texts: list[str]) -> dict:
    """
    INCREMENTAL UPSERT: Split → Embed → Push to Vertex AI Vector Search
    """
    chunks, ids = [], []

    for text in texts:
        for chunk in splitter.split_text(text):
            doc_id = str(uuid.uuid4())
            doc_store[doc_id] = {"text": chunk}
            chunks.append(chunk)
            ids.append(doc_id)

    # Get embeddings
    embeddings = embedder.embed_documents(chunks)

    # Upsert into Vertex AI Vector Search (stream update = incremental)
    index = MatchingEngineIndex(INDEX_ID)
    datapoints = [
        {
            "datapoint_id": ids[i],
            "feature_vector": embeddings[i],
        }
        for i in range(len(ids))
    ]
    index.upsert_datapoints(datapoints=datapoints)

    return {"added_chunks": len(chunks), "ids": ids}


def query_rag(question: str, top_k: int = 3) -> dict:
    """
    QUERY: Embed question → Search Vertex AI → LLM answer
    """
    # 1. Embed the question
    q_embedding = embedder.embed_query(question)

    # 2. Search Vertex AI Vector Search
    endpoint = MatchingEngineIndexEndpoint(INDEX_ENDPOINT_ID)
    results  = endpoint.find_neighbors(
        deployed_index_id=DEPLOYED_INDEX_ID,
        queries=[q_embedding],
        num_neighbors=top_k,
    )

    # 3. Retrieve matched chunks from doc_store
    neighbors  = results[0]  # first query's results
    context_chunks = []
    for neighbor in neighbors:
        doc_id = neighbor.id
        if doc_id in doc_store:
            context_chunks.append(doc_store[doc_id]["text"])

    if not context_chunks:
        return {"answer": "No relevant context found.", "context": []}

    # 4. Build prompt & call LLM
    context  = "\n\n".join(context_chunks)
    prompt   = f"""Answer using ONLY the context below.

Context:
{context}

Question: {question}

Answer:"""

    response = llm.invoke(prompt)
    return {
        "answer":  response.content,
        "context": context_chunks,
    }