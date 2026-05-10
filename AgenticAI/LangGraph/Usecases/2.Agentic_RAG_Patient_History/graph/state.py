"""
graph/state.py — ONE state shared by both Simple RAG and Agentic RAG graphs.

Both graphs use RAGState. The only difference is how they populate it:
  Simple RAG:  searches once → answer in one LLM call
  Agentic RAG: searches → reasons → decides to search again → loops → answers

Having one state makes it easy to swap graphs — same input, same output shape.
"""

from typing import TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class RAGState(TypedDict):
    # Original question from the doctor
    question: str

    # Full message history — add_messages APPENDS (never overwrites)
    messages: Annotated[list[BaseMessage], add_messages]

    # Accumulated retrieved text across all search rounds
    retrieved_context: str

    # Search history — each entry: {"query": str, "chunks": int}
    # Shown in UI as the "agentic trace" — empty for simple RAG
    search_log: list[dict]

    # Final answer — set by the last node before END
    final_answer: Optional[str]

    # Counts LLM reasoning rounds — safety guard for agentic loop
    iteration_count: int
