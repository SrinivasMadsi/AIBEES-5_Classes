"""
nodes/agents/retriever.py
──────────────────────────
Sub-agent: retriever_node
Performs broad and targeted retrieval from the FAISS vector store.
Uses RETRIEVER_TOOLS only.

AGENTIC RAG KEY POINT:
  This agent does NOT just do one search. It calls search_patient_records()
  with different queries on each tool call — broad first, then specific.
  The agent decides what to search based on what it found previously.
  This iterative retrieval is what makes it AGENTIC RAG vs simple RAG.
"""

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from graph.state import PatientHistoryState
from core.prompts import get_agent_prompt
from core.tools import RETRIEVER_TOOLS
from utils.llm import get_llm


def _run_sub_agent(state, agent_name, tools, max_iterations=8):
    """Shared mini agent loop reused by all sub-agents."""
    system      = SystemMessage(content=get_agent_prompt(agent_name))
    llm         = get_llm().bind_tools(tools)
    tool_runner = ToolNode(tools)
    local_msgs  = [system] + list(state["messages"])
    iterations  = 0

    while iterations < max_iterations:
        response = llm.invoke(local_msgs)
        local_msgs.append(response)
        iterations += 1
        if not response.tool_calls:
            break
        print(f"  Tools called: {[tc['name'] for tc in response.tool_calls]}")
        result = tool_runner.invoke({"messages": local_msgs})
        local_msgs.extend(result["messages"])

    for msg in reversed(local_msgs):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            print(f"  Findings ready ({len(msg.content)} chars)")
            return msg.content
    return "No findings produced."


def retriever_node(state: PatientHistoryState) -> dict:
    print("\n[retriever]")
    findings = _run_sub_agent(state, "retriever", RETRIEVER_TOOLS)
    existing = state.get("agent_findings", {})

    # Also accumulate raw context for later agents
    existing_ctx = state.get("retrieved_context", "")
    return {
        "agent_findings":   {**existing, "retriever": findings},
        "retrieved_context": existing_ctx + "\n\n" + findings,
        "messages":         [AIMessage(content=f"[retriever] {findings[:200]}...")],
    }
