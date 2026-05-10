"""
graph/builder.py — builds BOTH graphs.

LOOSELY COUPLED DESIGN:
  Both graphs are built here. To remove one:
    Comment out the import and the build function.
    Nothing else in the codebase needs to change.

Graph 1 — Simple RAG:
  START → rag_search → rag_simple → END
  (linear, no loop, one search, one LLM call)

Graph 2 — Agentic RAG:
  START → rag_search → rag_reason → should_continue
                            ↑              ↓ search again
                            └──── rag_search
                                   ↓ final answer
                               rag_answer → END

WHY BOTH ARE PROPER StateGraphs:
  Both are compiled LangGraph StateGraph objects.
  This means Langfuse shows BOTH as graph visualisations —
  not flat spans. You can see the loop in the agentic graph.

PNG files saved to project root:
  graph_simple.png  — the simple RAG flow
  graph_agentic.png — the agentic RAG loop
"""

from pathlib import Path
from langgraph.graph import StateGraph, START, END

from graph.state import RAGState
from graph.edges import should_continue
from nodes.rag_search import rag_search_node

# ── Simple RAG nodes ── comment this import to remove Simple RAG ───────────
from nodes.rag_simple import rag_simple_node

# ── Agentic RAG nodes ── comment this import to remove Agentic RAG ─────────
from nodes.rag_agent import rag_reason_node, rag_answer_node


def build_simple_graph():
    """
    Simple RAG: one search → one LLM call → answer.
    No loop. No reasoning about whether more info is needed.

    To REMOVE Simple RAG: comment out this function and its import in app.py.
    """
    builder = StateGraph(RAGState)
    builder.add_node("rag_search", rag_search_node)
    builder.add_node("rag_simple", rag_simple_node)
    builder.add_edge(START,        "rag_search")
    builder.add_edge("rag_search", "rag_simple")
    builder.add_edge("rag_simple", END)
    return builder.compile()


def build_agentic_graph():
    """
    Agentic RAG: search → reason → decide → (search again?) → answer.
    The LLM drives the loop — it decides when it has enough information.

    To REMOVE Agentic RAG: comment out this function and its import in app.py.
    """
    builder = StateGraph(RAGState)
    builder.add_node("rag_search", rag_search_node)
    builder.add_node("rag_reason", rag_reason_node)
    builder.add_node("rag_answer", rag_answer_node)

    builder.add_edge(START,        "rag_search")
    builder.add_edge("rag_search", "rag_reason")
    builder.add_edge("rag_answer", END)

    # Conditional edge — the loop mechanism
    builder.add_conditional_edges(
        "rag_reason",
        should_continue,
        {
            "rag_search": "rag_search",   # search again with new query
            "rag_answer": "rag_answer",   # done — extract final answer
        },
    )
    return builder.compile()


def save_graph_pngs() -> None:
    """
    Saves both graph PNGs to the project root.
    Called once on startup (from app.py session state init or main.py).
    """
    root = Path(__file__).parent.parent

    try:
        simple  = build_simple_graph()
        p = root / "graph_simple.png"
        p.write_bytes(simple.get_graph().draw_mermaid_png())
        print(f"Saved → {p}")
    except Exception as e:
        print(f"graph_simple.png failed: {e}")

    try:
        agentic = build_agentic_graph()
        p = root / "graph_agentic.png"
        p.write_bytes(agentic.get_graph().draw_mermaid_png())
        print(f"Saved → {p}")
    except Exception as e:
        print(f"graph_agentic.png failed: {e}")
