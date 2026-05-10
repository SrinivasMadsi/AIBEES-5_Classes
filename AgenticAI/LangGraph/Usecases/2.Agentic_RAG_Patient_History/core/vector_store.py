"""
core/vector_store.py — FAISS ingestion and retrieval.
Extract → MD5 dedup → chunk → embed → merge into combined index.
"""

import json, hashlib, fitz
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import COMBINED_INDEX, REGISTRY_FILE, FAISS_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K
from utils.embeddings import get_embeddings

FAISS_DIR.mkdir(parents=True, exist_ok=True)


def _load_registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text()) if REGISTRY_FILE.exists() else {}

def _save_registry(reg: dict):
    REGISTRY_FILE.write_text(json.dumps(reg, indent=2))

def extract_text(pdf_bytes: bytes) -> str:
    return "\n".join(p.get_text() for p in fitz.open(stream=pdf_bytes, filetype="pdf"))

def ingest_pdf(pdf_bytes: bytes, filename: str) -> tuple[bool, str]:
    reg  = _load_registry()
    text = extract_text(pdf_bytes)
    md5  = hashlib.md5(text.encode()).hexdigest()
    if md5 in reg:
        return False, f"'{filename}' already ingested."
    chunks    = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    ).split_text(text)
    emb       = get_embeddings()
    new_store = FAISS.from_texts(chunks, emb)
    if COMBINED_INDEX.exists():
        combined = FAISS.load_local(str(COMBINED_INDEX), emb, allow_dangerous_deserialization=True)
        combined.merge_from(new_store)
    else:
        combined = new_store
    combined.save_local(str(COMBINED_INDEX))
    reg[md5] = filename
    _save_registry(reg)
    return True, f"'{filename}' ingested successfully."

def load_index():
    if COMBINED_INDEX.exists():
        return FAISS.load_local(str(COMBINED_INDEX), get_embeddings(),
                                allow_dangerous_deserialization=True)
    return None

def search_records(query: str, k: int = TOP_K) -> list[str]:
    idx = load_index()
    if not idx:
        return ["No patient records ingested yet."]
    return [d.page_content.strip() for d in idx.similarity_search(query, k=k)]

def get_ingested_files() -> list[str]:
    return list(_load_registry().values())
