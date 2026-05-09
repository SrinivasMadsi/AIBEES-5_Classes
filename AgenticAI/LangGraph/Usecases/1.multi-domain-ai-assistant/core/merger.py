"""
core/merger.py
Response merger node — synthesises multi-domain agent responses.

For single-domain queries: passes through directly.
For multi-domain queries : uses LLM to merge into one coherent answer.
"""

from langchain_core.messages import HumanMessage
from core.llm import get_llm
from core.state import AgentState

DOMAIN_ICONS = {
    "licensing": "🔑",
    "onprem":    "🖥️",
    "kb_domain": "📚",
}


def merger_node(state: AgentState) -> AgentState:
    """
    Merger node — last node before END in the LangGraph.

    Single domain → pass through directly (no LLM call needed).
    Multi domain  → synthesise with LLM into one clean answer.
    """
    domain_responses = state.get("domain_responses", {})

    # ── Single domain: pass through ───────────────────────────────────────────
    if len(domain_responses) == 1:
        final = list(domain_responses.values())[0]
        return {**state, "response": final}

    # ── Multi domain: synthesise ──────────────────────────────────────────────
    print("\n🔀 [Merger] Combining multi-domain responses...")
    llm = get_llm(temperature=0.1)

    sections = []
    for domain, resp in domain_responses.items():
        icon  = DOMAIN_ICONS.get(domain, "📌")
        label = domain.upper().replace("_", " ")
        sections.append(f"{icon} {label} AGENT RESPONSE:\n{resp}")

    separator    = "\n\n---\n\n"
    sections_str = separator.join(sections)

    merge_prompt = f"""The user asked: {state["query"]}

You received responses from multiple domain agents:

{sections_str}

Synthesize these into ONE clear, well-structured final answer.
Clearly label each domain section. Do not repeat information.
Keep it concise and professional."""

    merged = llm.invoke([HumanMessage(content=merge_prompt)])

    content = merged.content
    if isinstance(content, list):
        content = "\n".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )

    print("  ✅ Responses merged successfully.")
    return {**state, "response": content.strip()}
