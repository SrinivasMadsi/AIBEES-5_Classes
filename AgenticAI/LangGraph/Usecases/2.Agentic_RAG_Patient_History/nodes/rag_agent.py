"""
nodes/rag_agent.py — Agentic RAG: reason node + answer node.

TWO nodes live here — both belong to the agentic loop:

  rag_reason_node:
    LLM reads retrieved chunks and decides:
      a) "I need more info" → outputs a NEW search query (plain text)
      b) "I have enough"   → outputs "FINAL ANSWER: <answer>"
    The conditional edge (edges.py → should_continue) reads this output
    and routes back to rag_search_node OR forward to rag_answer_node.

  rag_answer_node:
    Extracts the final answer from the last AIMessage.
    If the LLM already wrote "FINAL ANSWER: ...", extract it.
    If safety fallback triggered (max iterations), synthesise from context.

LOOSELY COUPLED DESIGN:
  To remove Agentic RAG from the app:
    In graph/builder.py comment out:
      # from nodes.rag_agent import rag_reason_node, rag_answer_node
      # def build_agentic_graph(): ...
    In app.py comment out:
      # agentic_graph = build_agentic_graph()
  Zero other changes needed.
"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import RAGState
from core.prompts import AGENTIC_RAG_SYSTEM
from utils.llm import get_llm


def rag_reason_node(state: RAGState) -> dict:
    """
    LLM reasoning node — runs on every agentic loop iteration.

    Reads the full message history (original question + all search results so far)
    and decides: output a new search query OR output "FINAL ANSWER: ...".

    This is the core of Agentic RAG — the LLM is in the driver's seat,
    deciding what information it still needs before it can answer safely.
    """
    iteration = state.get("iteration_count", 0) + 1
    print(f"\n[rag_reason] Iteration {iteration}")

    system   = SystemMessage(content=AGENTIC_RAG_SYSTEM)
    # Full history: original question + all search results + all prior reasoning
    messages = [system] + list(state.get("messages", []))

    # Add iteration context so LLM knows how many searches it has done
    search_log = state.get("search_log", [])
    if search_log:
        searches_done = len(search_log)
        remaining     = 4 - searches_done
        hint = HumanMessage(content=(
            f"You have searched {searches_done} time(s) so far. "
            f"You can search {remaining} more time(s) before you must answer. "
            f"If you have enough information, output your FINAL ANSWER now."
        ))
        messages.append(hint)

    response  = get_llm().invoke(messages)
    content   = response.content.strip()

    if content.startswith("FINAL ANSWER:"):
        print(f"  LLM decision: FINAL ANSWER")
    else:
        print(f"  LLM decision: search again → '{content[:60]}'")

    return {
        "messages":        [AIMessage(content=content)],
        "iteration_count": iteration,
    }


def rag_answer_node(state: RAGState) -> dict:
    """
    Extracts the final answer from state.
    If LLM wrote "FINAL ANSWER: ...", extract cleanly.
    If max iterations forced us here, synthesise from all retrieved context.
    """
    print("\n[rag_answer] Extracting final answer")

    messages = state.get("messages", [])

    # Walk backwards — find the last AIMessage with FINAL ANSWER
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content.strip().startswith("FINAL ANSWER:"):
            answer = msg.content.strip().removeprefix("FINAL ANSWER:").strip()
            print(f"  Extracted from FINAL ANSWER tag ({len(answer)} chars)")
            return {"final_answer": answer}

    # Safety fallback — synthesise from all retrieved context
    print("  Safety fallback — synthesising from retrieved context")
    context  = state.get("retrieved_context", "No records retrieved.")
    question = state["question"]
    prompt   = [
        SystemMessage(content="You are a medical AI. Answer based only on the retrieved records below."),
        HumanMessage(content=f"Records:\n{context}\n\nQuestion: {question}\nAnswer:"),
    ]
    answer = get_llm().invoke(prompt).content.strip()
    return {"final_answer": answer}
