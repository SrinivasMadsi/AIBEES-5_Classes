"""
graph/edges.py — all edge functions for both graphs.

Simple RAG graph:   START → search → answer → END  (no conditional edge needed)
Agentic RAG graph:  START → search → reason → should_continue → search/answer
                                              ↑___________________________|

should_continue reads the last AIMessage:
  - If it starts with "FINAL ANSWER:" → route to answer node
  - Otherwise treat the content as a new search query → route to search node
  - If max iterations reached → force to answer node
"""

from typing import Literal
from langchain_core.messages import AIMessage
from graph.state import RAGState
from config import MAX_AGENT_ITERATIONS


def should_continue(state: RAGState) -> Literal["rag_search", "rag_answer"]:
    """
    Conditional edge for the Agentic RAG graph.
    Reads last AIMessage to decide: search again or produce final answer.
    """
    if state.get("iteration_count", 0) >= MAX_AGENT_ITERATIONS:
        print(f"  [SAFETY] Max iterations reached — routing to answer")
        return "rag_answer"

    messages = state.get("messages", [])
    if not messages:
        return "rag_answer"

    last = messages[-1]
    if isinstance(last, AIMessage) and last.content:
        if last.content.strip().startswith("FINAL ANSWER:"):
            return "rag_answer"
        return "rag_search"

    return "rag_answer"
