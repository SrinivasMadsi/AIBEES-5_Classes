"""
Document loading and processing utilities for the RAG system.
Supports PDF and TXT files.
"""

import os
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import Config


class UnsupportedFileTypeError(ValueError):
    """Raised when an unsupported file extension is encountered."""
    pass


# Supported extensions and their loader classes
_LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
}


def load_and_process_document(file_path: Optional[str] = None) -> List[Document]:
    """
    Load a document from disk and split it into overlapping chunks.

    Args:
        file_path: Path to the document. Defaults to Config.PDF_PATH.

    Returns:
        List of chunked Document objects.

    Raises:
        FileNotFoundError: File does not exist.
        UnsupportedFileTypeError: Extension is not .pdf or .txt.
        ValueError: Loading or splitting failed.
    """
    target = file_path or Config.PDF_PATH

    if not os.path.exists(target):
        raise FileNotFoundError(f"File not found: {target}")

    loader = _get_loader(target)

    try:
        documents = loader.load()
        return _split(documents)
    except Exception as exc:
        raise ValueError(f"Error processing '{target}': {exc}") from exc


def is_supported(file_path: str) -> bool:
    """Return True if the file extension is supported."""
    return _ext(file_path) in _LOADER_MAP


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def _get_loader(path: str):
    ext = _ext(path)
    loader_cls = _LOADER_MAP.get(ext)
    if loader_cls is None:
        supported = ", ".join(_LOADER_MAP)
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Supported: {supported}"
        )
    return loader_cls(path)


def _split(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)
