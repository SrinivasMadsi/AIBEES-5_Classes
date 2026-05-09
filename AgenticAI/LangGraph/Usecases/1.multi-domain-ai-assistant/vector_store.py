"""
vector_store.py
Builds and loads domain-scoped FAISS vector stores.
Each domain gets its own separate index — core to domain isolation.
"""

import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config.settings import settings
from langchain_google_vertexai import VertexAIEmbeddings

DOMAIN_KB_PATHS = {
    "licensing":  "data/licensing/kb/",
    "onprem":     "data/onprem/kb/",
    "kb_domain":  "data/kb_domain/kb/",
}


def get_embeddings():
    return VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=settings.gcp_project_id,
        location=settings.gcp_region,
    )


def load_documents(folder_path: str) -> list:
    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                content = f.read()
            docs.append(Document(
                page_content=content,
                metadata={"source": filename, "domain": folder_path}
            ))
    return docs


def build_vector_stores():
    embeddings = get_embeddings()
    os.makedirs(settings.vector_store_path, exist_ok=True)

    for domain, kb_path in DOMAIN_KB_PATHS.items():
        print(f"📦 Building vector store for domain: {domain}")
        docs = load_documents(kb_path)
        if not docs:
            print(f"  ⚠️  No documents found in {kb_path}")
            continue
        vectorstore = FAISS.from_documents(docs, embeddings)
        save_path   = os.path.join(settings.vector_store_path, domain)
        vectorstore.save_local(save_path)
        print(f"  ✅ Saved {len(docs)} docs → {save_path}")

    print("\n✅ All domain vector stores built successfully!")


if __name__ == "__main__":
    build_vector_stores()
