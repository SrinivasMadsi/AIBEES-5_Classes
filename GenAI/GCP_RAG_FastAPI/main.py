"""
FastAPI is a Python web framework for building APIs.
It lets you expose Python functions as HTTP endpoints
that any client (browser, Postman, mobile app) can call
over the internet using HTTP methods like GET and POST.

In this code, we create a FastAPI app with two main endpoints:
FastAPI app with 2 endpoints:
  POST /add    → Upload PDF, extract text, add to Vector Search
  POST /query  → RAG query against stored documents
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel # for request validation 
from rag_engine import add_documents, query_rag
import fitz  # PyMuPDF

app = FastAPI(
    title="Incremental RAG with Google Vector Search",
    description="Simple RAG demo using Vertex AI Vector Search + Gemini",
    version="1.0.0",
)

# ── Request Model ─────────────────────────────────────────
"""
Pydantic model for validating the query request payload.
   With BaseModel → Pydantic validates automatically:
     Client sends: {}                  → 422 error: question is required
     Client sends: {"question": 123}   → 422 error: question must be str
     Client sends: {"question": "hi"}  → ✅ request.question = "hi"
                                           request.top_k    = 3 (default)
"""
class QueryRequest(BaseModel):
    question: str
    top_k: int = 3

# ── API 1: Upload PDF ─────────────────────────────────────
"""
@app.post is a DECORATOR — it registers the function below it as an HTTP endpoint that listens for POST requests.
@app       → the FastAPI application instance
.post      → HTTP method: POST (used to SEND data to server)
("/add")   → the URL path: http://localhost:8000/add
async      → the function is asynchronous, allowing many requests to be handled concurrently without blocking
"""
@app.post("/add", summary="Upload a PDF and add to Vector Search")
async def add_pdf(file: UploadFile = File(..., description="Upload a PDF file")):
    """
    1. Accepts a PDF via file upload
    2. Extracts text using PyMuPDF
    3. Splits → Embeds → Upserts into Google Vertex AI Vector Search
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read and extract text from PDF
    pdf_bytes = await file.read()
    pdf_doc   = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text = ""
    for page in pdf_doc:
        full_text += page.get_text()

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="PDF has no extractable text")

    # Add to Vector Search
    result = add_documents([full_text])

    return {
        "status":       "success",
        "filename":     file.filename,
        "pages":        len(pdf_doc),
        "added_chunks": result["added_chunks"],
        "chunk_ids":    result["ids"],
    }


# ── API 2: Query RAG ──────────────────────────────────────
@app.post("/query", summary="Query the RAG pipeline")
async def query(request: QueryRequest):
    """
    Embeds the question → finds nearest chunks → Gemini generates answer
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is empty")

    result = query_rag(request.question, top_k=request.top_k)
    return {"status": "success", **result}


# ── Health Check ──────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Incremental RAG API is running!"}
