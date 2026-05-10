"""
nodes/agents/flagger.py — Sub-agent: flagger_node
Identifies critical flags, allergies, and urgent safety issues. Uses FLAGGER_TOOLS.
Runs LAST — reads all prior agent_findings before flagging.
"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from graph.state import PatientHistoryState
from core.prompts import get_agent_prompt
from core.tools import FLAGGER_TOOLS
from utils.llm import get_llm


def flagger_node(state: PatientHistoryState) -> dict:
    print("\n[flagger]")

    agent_findings = state.get("agent_findings", {})
    findings_ctx   = "\nContext from prior agents:\n" + "\n".join(
        f"{k.upper()}:\n{v}" for k, v in agent_findings.items()
    )

    system      = SystemMessage(content=get_agent_prompt("flagger"))
    context_msg = HumanMessage(content=findings_ctx + "\nNow identify all critical flags.")
    llm         = get_llm().bind_tools(FLAGGER_TOOLS)
    tool_runner = ToolNode(FLAGGER_TOOLS)

    local_msgs = [system] + list(state["messages"]) + [context_msg]
    iterations = 0

    while iterations < 6:
        response = llm.invoke(local_msgs)
        local_msgs.append(response)
        iterations += 1
        if not response.tool_calls:
            break
        print(f"  Tools called: {[tc['name'] for tc in response.tool_calls]}")
        result = tool_runner.invoke({"messages": local_msgs})
        local_msgs.extend(result["messages"])

    findings = ""
    for msg in reversed(local_msgs):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            findings = msg.content
            break

    print(f"  Flags ready ({len(findings)} chars)")
    existing = state.get("agent_findings", {})
    return {
        "agent_findings": {**existing, "flagger": findings},
        "messages":       [AIMessage(content=f"[flagger] {findings[:200]}...")],
    }
