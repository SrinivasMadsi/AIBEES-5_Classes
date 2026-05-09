"""
agents/kb/tools.py
Tools scoped EXCLUSIVELY to the KB domain.
"""

import os
import sqlite3
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from config.settings import settings


def get_embeddings():
    return VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=settings.gcp_project_id,
        location=settings.gcp_region,
    )


def _read_sharepoint(query: str) -> str:
    folder = "data/kb_domain/sharepoint/"
    if not os.path.exists(folder):
        return "No KB SharePoint documents found."
    results = []
    for filename in os.listdir(folder):
        if not filename.endswith(".txt"):
            continue
        with open(os.path.join(folder, filename), "r") as f:
            content = f.read()
        if any(word in content.lower() for word in query.lower().split()):
            results.append(f"[{filename}]\n{content[:800]}...")
    return "\n\n---\n\n".join(results) if results else "No relevant KB SharePoint docs found."


def _run_sql(sql: str) -> str:
    try:
        conn = sqlite3.connect(settings.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "Query returned no results."
        cols   = rows[0].keys()
        output = " | ".join(cols) + "\n" + "-"*60 + "\n"
        output += "\n".join(" | ".join(str(v) for v in row) for row in rows)
        return output
    except Exception as e:
        return f"SQL Error: {str(e)}"


@tool
def kb_sharepoint_search(query: str) -> str:
    """Search KB domain SharePoint documents for governance guides and policies."""
    return _read_sharepoint(query)


@tool
def kb_kb_search(query: str) -> str:
    """Search the KB domain Knowledge Base using semantic search (FAISS)."""
    try:
        store = FAISS.load_local(
            os.path.join(settings.vector_store_path, "kb_domain"),
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        docs = store.similarity_search(query, k=3)
        if not docs:
            return "No relevant KB domain articles found."
        return "\n\n---\n\n".join(
            f"[{doc.metadata.get('source')}]\n{doc.page_content[:600]}"
            for doc in docs
        )
    except Exception as e:
        return f"KB Search Error: {str(e)}"


@tool
def kb_nl2sql(natural_language_query: str) -> str:
    """
    Query the KB domain database using natural language.
    Tables: kb_smart_accounts, kb_articles.
    """
    q = natural_language_query.lower()

    if "smart account" in q and ("list" in q or "all" in q or "active" in q):
        sql = "SELECT author_name, email, specialization, articles_authored, status FROM kb_smart_accounts WHERE account_type = 'SMART'"
    elif "virtual account" in q:
        sql = "SELECT author_name, email, account_type, status FROM kb_smart_accounts WHERE account_type = 'VIRTUAL'"
    elif "probation" in q:
        sql = "SELECT author_name, email, specialization, joined_date FROM kb_smart_accounts WHERE status = 'Probation'"
    elif "most viewed" in q or "top" in q or "popular" in q:
        sql = """SELECT a.title, a.category, s.author_name, a.views, a.rating
                 FROM kb_articles a JOIN kb_smart_accounts s ON a.author_id = s.id
                 ORDER BY a.views DESC LIMIT 5"""
    elif "draft" in q:
        sql = """SELECT a.title, a.category, s.author_name FROM kb_articles a
                 JOIN kb_smart_accounts s ON a.author_id = s.id WHERE a.status = 'Draft'"""
    elif "rating" in q or "highly rated" in q:
        sql = """SELECT title, category, rating, views FROM kb_articles
                 WHERE status = 'Published' ORDER BY rating DESC LIMIT 5"""
    else:
        sql = "SELECT author_name, account_type, specialization, articles_authored, status FROM kb_smart_accounts"

    return f"[SQL]\n{sql}\n\n[Results]\n{_run_sql(sql)}"


# ── Tool registry for this domain ─────────────────────────────────────────────
KB_TOOLS = [
    kb_sharepoint_search,
    kb_kb_search,
    kb_nl2sql,
]
