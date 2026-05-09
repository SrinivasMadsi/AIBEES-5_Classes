"""
agents/onprem/tools.py
Tools scoped EXCLUSIVELY to the OnPrem domain.

These tools only access OnPrem data:
  - OnPrem SharePoint folder
  - OnPrem FAISS index
  - OnPrem SQL tables (onprem_smart_accounts, onprem_virtual_accounts, onprem_servers)
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
    folder = "data/onprem/sharepoint/"
    if not os.path.exists(folder):
        return "No OnPrem SharePoint documents found."
    results = []
    for filename in os.listdir(folder):
        if not filename.endswith(".txt"):
            continue
        with open(os.path.join(folder, filename), "r") as f:
            content = f.read()
        if any(word in content.lower() for word in query.lower().split()):
            results.append(f"[{filename}]\n{content[:800]}...")
    return "\n\n---\n\n".join(results) if results else "No relevant OnPrem SharePoint docs found."


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
def onprem_sharepoint_search(query: str) -> str:
    """Search OnPrem SharePoint documents for setup guides and infrastructure policies."""
    return _read_sharepoint(query)


@tool
def onprem_kb_search(query: str) -> str:
    """Search the OnPrem Knowledge Base using semantic search (FAISS)."""
    try:
        store = FAISS.load_local(
            os.path.join(settings.vector_store_path, "onprem"),
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        docs = store.similarity_search(query, k=3)
        if not docs:
            return "No relevant OnPrem KB articles found."
        return "\n\n---\n\n".join(
            f"[{doc.metadata.get('source')}]\n{doc.page_content[:600]}"
            for doc in docs
        )
    except Exception as e:
        return f"KB Search Error: {str(e)}"


@tool
def onprem_nl2sql(natural_language_query: str) -> str:
    """
    Query the OnPrem database using natural language.
    Tables: onprem_smart_accounts, onprem_virtual_accounts, onprem_servers.
    """
    q = natural_language_query.lower()

    if "break" in q and ("glass" in q or "emergency" in q):
        sql = "SELECT account_name, account_type, status, data_center, last_login FROM onprem_smart_accounts WHERE account_type = 'BREAK_GLASS'"
    elif "disabled" in q or "locked" in q:
        sql = "SELECT account_name, account_type, status, owner_team FROM onprem_smart_accounts WHERE status IN ('Disabled','Locked')"
    elif "tier 1" in q or "tier1" in q or "mission critical" in q:
        sql = "SELECT hostname, ip_address, data_center, os, status FROM onprem_servers WHERE tier = 'Tier1'"
    elif "server" in q and ("list" in q or "all" in q or "active" in q):
        sql = "SELECT hostname, data_center, tier, os, status, owner_team FROM onprem_servers WHERE status = 'Active'"
    elif "virtual account" in q:
        sql = """SELECT ova.virtual_account_name, osa.account_name, ova.resource_type,
                        ova.cpu_allocated, ova.ram_gb_allocated, ova.status
                 FROM onprem_virtual_accounts ova
                 JOIN onprem_smart_accounts osa ON ova.smart_account_id = osa.id"""
    elif "dc-hq" in q or "hq" in q:
        sql = "SELECT hostname, ip_address, tier, os, status FROM onprem_servers WHERE data_center = 'DC-HQ'"
    elif "smart account" in q:
        sql = "SELECT account_name, account_type, status, data_center, owner_team FROM onprem_smart_accounts"
    else:
        sql = "SELECT hostname, data_center, tier, status FROM onprem_servers LIMIT 10"

    return f"[SQL]\n{sql}\n\n[Results]\n{_run_sql(sql)}"


# ── Tool registry for this domain ─────────────────────────────────────────────
ONPREM_TOOLS = [
    onprem_sharepoint_search,
    onprem_kb_search,
    onprem_nl2sql,
]
