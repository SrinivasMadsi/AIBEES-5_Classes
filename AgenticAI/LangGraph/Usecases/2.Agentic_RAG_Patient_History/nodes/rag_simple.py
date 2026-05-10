"""
nodes/rag_simple.py — Simple RAG answer node.

LOOSELY COUPLED DESIGN:
  To remove Simple RAG from the app:
    In graph/builder.py comment out:
      # from nodes.rag_simple import rag_simple_node
      # def build_simple_graph(): ...
    In app.py comment out:
      # simple_graph = build_simple_graph()
  That's it — zero other changes needed.

What this node does:
  Reads ALL retrieved chunks from state (fetched by rag_search_node),
  calls the LLM ONCE, and produces the final answer.
  No reasoning loop. No second search. One pass.

This is the key difference from Agentic RAG:
  Simple RAG: search_node → simple_answer_node → END
  Agentic RAG: search_node → reason_node → (loop) → answer_node → END
"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import RAGState
from core.prompts import SIMPLE_RAG_SYSTEM
from utils.llm import get_llm


def rag_simple_node(state: RAGState) -> dict:
    """One LLM call over all retrieved context. No iteration."""
    print("\n[rag_simple] Answering from retrieved context (single pass)")

    question = state["question"]

    # Use the formatted HumanMessage added by rag_search_node (nicely formatted
    # [Excerpt N] blocks) rather than the raw retrieved_context string.
    # rag_search_node appends a HumanMessage with "Search results for: ..." content.
    state_messages = state.get("messages", [])
    search_context = ""
    for msg in state_messages:
        if isinstance(msg, HumanMessage) and msg.content and "Search results for:" in msg.content:
            search_context = msg.content
            break

    # Fallback to retrieved_context if the formatted message isn't found
    if not search_context:
        search_context = state.get("retrieved_context", "No records found.")

    messages = [
        SystemMessage(content=SIMPLE_RAG_SYSTEM),
        HumanMessage(content=f"{search_context}\n\nQuestion: {question}"),
    ]

    response = get_llm().invoke(messages)
    answer   = response.content.strip()
    print(f"  Answer ready ({len(answer)} chars)")

    return {
        "messages":     [AIMessage(content=answer)],
        "final_answer": answer,
        # Explicitly preserve search_log so it is always available in the result
        "search_log":   state.get("search_log", []),
    }