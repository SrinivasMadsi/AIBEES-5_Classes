"""
nodes/rag_search.py — FAISS search node shared by BOTH graphs.

Simple RAG uses this once.
Agentic RAG uses this on every loop iteration — with a different query each time.

In Agentic RAG, the query comes from the LLM's previous AIMessage.
In Simple RAG, the query is the original question from state.
"""

from langchain_core.messages import HumanMessage
from graph.state import RAGState
from core.vector_store import search_records


def rag_search_node(state: RAGState) -> dict:
    """
    Determines what to search, executes FAISS search, feeds results back.

    Query selection:
      - If last message is an AIMessage with content that is NOT "FINAL ANSWER:"
        → that content IS the next query (the agentic LLM wrote it)
      - Otherwise → use the original question (simple RAG first call)
    """
    from langchain_core.messages import AIMessage

    messages = state.get("messages", [])
    question = state["question"]

    # Determine query: agentic LLM writes its own query in the last AIMessage
    query = question   # default — used by simple RAG and first agentic call
    if messages:
        last = messages[-1]
        if (isinstance(last, AIMessage) and last.content
                and not last.content.strip().startswith("FINAL ANSWER:")):
            query = last.content.strip()

    print(f"\n[rag_search] '{query[:60]}'")
    chunks = search_records(query, k=5)

    # Format chunks for LLM
    context_text = f"Search results for: '{query}'\n\n"
    for i, chunk in enumerate(chunks, 1):
        context_text += f"[Excerpt {i}]:\n{chunk}\n\n"

    # Accumulate retrieved context and log
    existing_ctx = state.get("retrieved_context", "")
    existing_log = state.get("search_log", [])

    return {
        "messages":         [HumanMessage(content=context_text)],
        "retrieved_context": existing_ctx + f"\n\n=== Search: {query} ===\n" + "\n\n".join(chunks),
        "search_log":        existing_log + [{"query": query, "chunks": len(chunks)}],
    }
