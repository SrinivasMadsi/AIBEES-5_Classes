"""
agents/licensing/tools.py
Tools scoped EXCLUSIVELY to the Licensing domain.

These tools only access Licensing data:
  - Licensing SharePoint folder
  - Licensing FAISS index
  - Licensing SQL tables (licensing_smart_accounts, licensing_virtual_accounts)
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
    folder = "data/licensing/sharepoint/"
    if not os.path.exists(folder):
        return "No Licensing SharePoint documents found."
    results = []
    query_lower = query.lower()
    for filename in os.listdir(folder):
        if not filename.endswith(".txt"):
            continue
        with open(os.path.join(folder, filename), "r") as f:
            content = f.read()
        if any(word in content.lower() for word in query_lower.split()):
            results.append(f"[{filename}]\n{content[:800]}...")
    return "\n\n---\n\n".join(results) if results else "No relevant Licensing SharePoint docs found."


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
def licensing_sharepoint_search(query: str) -> str:
    """Search Licensing SharePoint documents for policies, guides, and procedures."""
    return _read_sharepoint(query)


@tool
def licensing_kb_search(query: str) -> str:
    """Search the Licensing Knowledge Base using semantic search (FAISS)."""
    try:
        store = FAISS.load_local(
            os.path.join(settings.vector_store_path, "licensing"),
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        docs = store.similarity_search(query, k=3)
        if not docs:
            return "No relevant Licensing KB articles found."
        return "\n\n---\n\n".join(
            f"[{doc.metadata.get('source')}]\n{doc.page_content[:600]}"
            for doc in docs
        )
    except Exception as e:
        return f"KB Search Error: {str(e)}"


@tool
def licensing_nl2sql(natural_language_query: str) -> str:
    """
    Query the Licensing database using natural language.
    Tables: licensing_smart_accounts, licensing_virtual_accounts.
    """
    q = natural_language_query.lower()

    if "out of compliance" in q or "non-compliant" in q:
        sql = """SELECT lsa.account_name, lva.virtual_account_name, lva.region,
                        lva.allocated_licenses, lva.used_licenses, lva.compliance_status
                 FROM licensing_virtual_accounts lva
                 JOIN licensing_smart_accounts lsa ON lva.smart_account_id = lsa.id
                 WHERE lva.compliance_status != 'Authorized'"""
    elif "suspended" in q:
        sql = "SELECT account_name, domain, status FROM licensing_smart_accounts WHERE status = 'Suspended'"
    elif "virtual account" in q:
        sql = """SELECT lva.virtual_account_name, lsa.account_name, lva.region,
                        lva.allocated_licenses, lva.used_licenses, lva.compliance_status
                 FROM licensing_virtual_accounts lva
                 JOIN licensing_smart_accounts lsa ON lva.smart_account_id = lsa.id"""
    elif "total" in q or "count" in q or "how many" in q:
        sql = "SELECT SUM(total_licenses) as total, SUM(used_licenses) as used FROM licensing_smart_accounts"
    else:
        sql = "SELECT account_name, domain, status, total_licenses, used_licenses FROM licensing_smart_accounts"

    return f"[SQL]\n{sql}\n\n[Results]\n{_run_sql(sql)}"


# ── Tool registry for this domain ─────────────────────────────────────────────
LICENSING_TOOLS = [
    licensing_sharepoint_search,
    licensing_kb_search,
    licensing_nl2sql,
]
