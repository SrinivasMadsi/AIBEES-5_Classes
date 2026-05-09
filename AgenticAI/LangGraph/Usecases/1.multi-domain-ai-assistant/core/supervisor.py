"""
core/supervisor.py
Supervisor agent — classifies domain and routes query.

Responsibilities:
  - Understand the user query
  - Classify into one or more domains
  - Explain the routing decision
  - Return updated state with domains + routing_reason
"""

from langchain_core.messages import HumanMessage, SystemMessage
from core.llm import get_llm
from core.state import AgentState

SUPERVISOR_PROMPT = """
You are an Enterprise AI Supervisor. Your job is to classify the user's
query into one or MORE of these three domains.

  licensing  → Software licenses, Smart Accounts (license management),
               Virtual Accounts (license containers), compliance, Cisco SSM,
               license counts, true-up, subscription, CCW, CSLU

  onprem     → On-premises infrastructure, servers, data centers,
               OnPrem Smart Accounts (admin/service accounts), virtual machines,
               resource pools, VMware, UCS, patching, backup, CMDB

  kb_domain  → Knowledge Base platform, KB authors,
               KB Smart Accounts (author accounts), KB Virtual Accounts
               (reader accounts), articles, Confluence, knowledge management

If the query mentions concepts from MULTIPLE domains, list ALL relevant
domains separated by commas.

Respond in EXACTLY this format (two lines only):
domains: <comma-separated: licensing, onprem, kb_domain>
reason: <one sentence explaining which domains are involved and why>
"""

VALID_DOMAINS = {"licensing", "onprem", "kb_domain"}


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor node — classifies query and sets routing in state.
    Called first by LangGraph before any domain agent runs.
    """
    print("\n🧠 [Supervisor] Classifying query domain(s)...")
    llm = get_llm(temperature=0.0)

    response = llm.invoke([
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=state["query"]),
    ])

    domains = ["kb_domain"]
    reason  = "Defaulted to kb_domain — could not parse supervisor response."

    for line in response.content.strip().splitlines():
        line = line.strip()
        if line.lower().startswith("domains:"):
            raw = line.split(":", 1)[1].strip().lower()
            domains = [d.strip() for d in raw.split(",") if d.strip() in VALID_DOMAINS]
        elif line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()

    if not domains:
        domains = ["kb_domain"]
        reason  = "No valid domain found — defaulted to kb_domain."

    is_multi = len(domains) > 1

    if is_multi:
        print(f"  🔀 Multi-domain query detected!")
        for d in domains:
            print(f"     → Routing to : {d.upper()} AGENT")
    else:
        print(f"  ✅ Routed to domain : {domains[0].upper()} AGENT")

    print(f"  💡 Routing reason   : {reason}")

    return {
        **state,
        "domains":         domains,
        "routing_reason":  reason,
        "is_multi_domain": is_multi,
        "domain_responses": {},
    }


def route_to_domain(state: AgentState) -> list:
    """
    Conditional edge function — maps domain names to node names.
    Returns a list so LangGraph can fan out to multiple agents.
    """
    domain_map = {
        "licensing": "licensing_agent",
        "onprem":    "onprem_agent",
        "kb_domain": "kb_agent",
    }
    nodes = [domain_map[d] for d in state["domains"] if d in domain_map]
    return nodes if nodes else ["kb_agent"]
