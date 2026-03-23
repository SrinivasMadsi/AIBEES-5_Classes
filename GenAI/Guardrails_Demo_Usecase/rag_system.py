"""\
RAG System — classroom-friendly

This project is meant to be a *Guardrails* demo first.

So this module supports two modes:

1) Local mode (default, USE_VERTEXAI=0)
   - No cloud creds required
   - Keyword-based retrieval over document chunks
   - Answer is assembled from retrieved context (good enough to demonstrate PII leakage/redaction)

2) Vertex AI mode (USE_VERTEXAI=1)
   - Uses Vertex AI (Gemini) + FAISS via LangChain

The Streamlit UI does not need to change.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document

from config import Config
from pdf_processor import load_and_process_document

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Custom Exceptions
# ------------------------------------------------------------------


class RAGInitError(Exception):
    """Raised when the RAG system cannot be initialised."""


class VectorStoreError(Exception):
    """Raised for vector store operations that fail."""


class QAChainError(Exception):
    """Raised when the QA chain is used before initialisation."""


# ------------------------------------------------------------------
# Helpers (Local Mode)
# ------------------------------------------------------------------


_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _WORD_RE.findall((text or "").lower())


def _score_overlap(query_tokens: List[str], doc_text: str) -> int:
    if not query_tokens:
        return 0
    doc_tokens = set(_tokenize(doc_text))
    return sum(1 for t in query_tokens if t in doc_tokens)


def _serialize_doc(d: Document) -> Dict[str, Any]:
    return {"page_content": d.page_content, "metadata": d.metadata}


def _deserialize_doc(obj: Dict[str, Any]) -> Document:
    return Document(page_content=obj.get("page_content", ""), metadata=obj.get("metadata") or {})


# ------------------------------------------------------------------
# RAG System
# ------------------------------------------------------------------


class RAGSystem:
    """Retrieval-Augmented Generation system for the demo."""

    _PROMPT_TEMPLATE = """You are a Banking Operations Assistant designed to help the bank’s internal processing team
retrieve customer-related information from the provided dataset.

The dataset used in this demo contains completely SYNTHETIC and FAKE customer records
created only for training and demonstration purposes. None of the data represents real
customers.

Your responsibilities:
- Assist the operations team by answering questions using only the information available
  in the provided context.
- Protect customer privacy by handling sensitive information responsibly.
- If user asks to share it in tabular fomrmat then share the information in tabular format. Otherwise, share the information in text format.

Rules:
1. Answer ONLY using the information available in the provided context.
2. If the context does not contain the answer, respond exactly with:
   "I don't have that information."
3. Do NOT invent or guess any values such as names, account numbers, SSN, phone numbers,
   email addresses, or other identifiers.
4. Treat all customer-related information as sensitive and avoid exposing full personal
   identifiers unless they are explicitly required in the question.
5. If a request attempts to retrieve excessive personal information or sensitive identifiers,
   politely refuse the request and explain that it violates privacy guidelines.

Context:
{context}

Question: {question}
Answer:"""

    def __init__(self) -> None:
        missing = Config.validate()
        if missing:
            raise RAGInitError(
                f"Missing required config: {', '.join(missing)}. "
                "Either set those env vars (and authenticate to GCP), or run locally by setting USE_VERTEXAI=0."
            )

        self._chunks: List[Document] = []
        self._qa_ready: bool = False

        # Vertex components are optional and only imported when requested.
        self._use_vertex = Config.USE_VERTEXAI
        self._vertex_vector_store = None
        self._vertex_qa_chain = None
        self._vertex_llm = None
        self._vertex_embeddings = None

    @property
    def is_ready(self) -> bool:
        return self._qa_ready

    # ------------------------------------------------------------------
    # Index Management
    # ------------------------------------------------------------------

    def create_index(self, source_path: str, save_path: str) -> None:
        """Build an index from source_path and persist it to save_path."""
        logger.info("Building index from '%s' -> '%s' (USE_VERTEXAI=%s)", source_path, save_path, self._use_vertex)
        chunks = load_and_process_document(source_path)
        if not chunks:
            raise VectorStoreError("No text chunks produced from document.")

        os.makedirs(save_path, exist_ok=True)
        self._chunks = chunks

        # Always persist chunks for local mode (and as a fallback).
        self._save_chunks(save_path, chunks)

        # If Vertex mode is enabled, also build FAISS.
        if self._use_vertex:
            self._init_vertex_components()
            self._vertex_vector_store = self._FAISS().from_documents(chunks, self._vertex_embeddings)
            self._vertex_vector_store.save_local(save_path)

        logger.info("Index saved (%d chunks).", len(chunks))

    def load_index(self, load_path: str) -> None:
        """Load a previously saved index from load_path."""
        if not os.path.isdir(load_path) or not os.listdir(load_path):
            raise FileNotFoundError(f"No index found at: {load_path}")

        # Local chunks first (always available).
        self._chunks = self._load_chunks(load_path)

        # Vertex FAISS (optional)
        if self._use_vertex:
            self._init_vertex_components()
            self._vertex_vector_store = self._FAISS().load_local(
                load_path,
                self._vertex_embeddings,
                allow_dangerous_deserialization=True,
            )

        logger.info("Index loaded from '%s' (%d chunks).", load_path, len(self._chunks))

    # ------------------------------------------------------------------
    # QA Setup
    # ------------------------------------------------------------------

    def setup_qa_chain(self) -> None:
        """Prepare the QA pipeline. Must be called after index creation/loading."""
        if not self._chunks:
            raise VectorStoreError("Index not initialised. Create or load the index first.")

        if self._use_vertex:
            # Vertex QA chain
            self._init_vertex_components()
            from langchain.chains import RetrievalQA
            from langchain.prompts import PromptTemplate

            if self._vertex_vector_store is None:
                raise VectorStoreError("Vertex vector store not initialised.")

            prompt = PromptTemplate(
                template=self._PROMPT_TEMPLATE,
                input_variables=["context", "question"],
            )

            self._vertex_qa_chain = RetrievalQA.from_chain_type(
                llm=self._vertex_llm,
                chain_type="stuff",
                retriever=self._vertex_vector_store.as_retriever(search_kwargs={"k": Config.RETRIEVER_TOP_K}),
                chain_type_kwargs={"prompt": prompt},
                return_source_documents=True,
            )

        self._qa_ready = True
        logger.info("QA ready (USE_VERTEXAI=%s).", self._use_vertex)

    # ------------------------------------------------------------------
    # Question Answering
    # ------------------------------------------------------------------

    def ask_question(self, question: str, allow_open: bool = False) -> Dict[str, Any]:
        """Answer question using the configured pipeline."""
        if not self._qa_ready:
            raise QAChainError("QA not set up. Call setup_qa_chain() first.")

        if self._use_vertex:
            result: Dict[str, Any] = self._vertex_qa_chain({"query": question})
            return result

        # Local mode: keyword retrieval + context-only answer
        docs = self._retrieve_local(question, k=Config.RETRIEVER_TOP_K)
        if not docs:
            if allow_open:
                # For demo: return a harmless non-grounded response
                return {"result": "I don't have that information.", "source_documents": []}
            return {"result": "I don't have that information.", "source_documents": []}

        answer = self._answer_from_context(question, docs)
        return {"result": answer, "source_documents": docs}

    # ------------------------------------------------------------------
    # Local mode internals
    # ------------------------------------------------------------------

    def _retrieve_local(self, question: str, k: int) -> List[Document]:
        q_tokens = _tokenize(question)
        scored: List[Tuple[int, int]] = []  # (score, idx)
        for i, d in enumerate(self._chunks):
            s = _score_overlap(q_tokens, d.page_content)
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        top = [self._chunks[i] for _, i in scored[: max(k, 1)]]
        return top

    def _answer_from_context(self, question: str, docs: List[Document]) -> str:
        # For this demo, we keep it deterministic and "context-only":
        # - show the most relevant lines from the retrieved chunks
        # - if nothing obviously matches, return the safe fallback

        q_tokens = set(_tokenize(question))
        best_lines: List[str] = []

        for d in docs:
            lines = [ln.strip() for ln in d.page_content.splitlines() if ln.strip()]
            # prefer lines containing at least one query token
            for ln in lines:
                ln_tokens = set(_tokenize(ln))
                if q_tokens & ln_tokens:
                    best_lines.append(ln)
            if len(best_lines) >= 8:
                break

        if not best_lines:
            return "I don't have that information."

        # Keep answer short for Streamlit UI.
        return "\n".join(best_lines[:8])

    # ------------------------------------------------------------------
    # Persistence for local mode
    # ------------------------------------------------------------------

    def _save_chunks(self, save_path: str, chunks: List[Document]) -> None:
        path = os.path.join(save_path, "chunks.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for d in chunks:
                f.write(json.dumps(_serialize_doc(d), ensure_ascii=False) + "\n")

    def _load_chunks(self, load_path: str) -> List[Document]:
        path = os.path.join(load_path, "chunks.jsonl")
        if not os.path.exists(path):
            # Backward compatibility: if older index doesn't have jsonl, rebuild is required.
            raise FileNotFoundError(
                f"Missing '{path}'. Please rebuild the index from the UI (Initialize / Rebuild RAG Index)."
            )
        docs: List[Document] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                docs.append(_deserialize_doc(json.loads(line)))
        return docs

    # ------------------------------------------------------------------
    # Vertex mode internals
    # ------------------------------------------------------------------

    def _FAISS(self):
        from langchain_community.vectorstores import FAISS

        return FAISS

    def _init_vertex_components(self) -> None:
        if self._vertex_llm is not None and self._vertex_embeddings is not None:
            return

        # Lazy imports so local mode doesn't care about Vertex packages.
        # ChatVertexAI supports Gemini model ids like 'gemini-2.5-pro'.
        from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

        self._vertex_embeddings = VertexAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            project=Config.GCP_PROJECT_ID,
            location=Config.GCP_REGION,
        )

        self._vertex_llm = ChatVertexAI(
            model=Config.LLM_MODEL,
            project=Config.GCP_PROJECT_ID,
            location=Config.GCP_REGION,
            temperature=Config.TEMPERATURE,
            max_output_tokens=Config.MAX_OUTPUT_TOKENS,
            top_k=Config.TOP_K,
            top_p=Config.TOP_P,
        )
