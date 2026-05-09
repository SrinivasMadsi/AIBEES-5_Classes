"""
multi_agent.py
Entry point — now thin and clean.

This file ONLY:
  1. Builds the graph
  2. Runs queries
  3. Formats output

All business logic lives in:
  core/       → graph, supervisor, merger, state, llm
  agents/     → licensing, onprem, kb (each self-contained)
  observability/ → Langfuse tracing
  config/     → settings

flowchart LR
    UQ(["👤 User Query"])
    SUP["🧠 Supervisor agent · LangGraph router"]
    subgraph LICENSING ["🔑 Licensing"]
        LA["agent"] --> LSP["SharePoint"]
        LA --> LKB["KB Search"]
        LA --> LSQL["NL2SQL"]
    end
    subgraph ONPREM ["🖥️ OnPrem"]
        OA["agent"] --> OSP["SharePoint"]
        OA --> OKB["KB Search"]
        OA --> OSQL["NL2SQL"]
    end
    subgraph KB ["📚 KB"]
        KA["agent"] --> KSP["SharePoint"]
        KA --> KKB["KB Search"]
        KA --> KSQL["NL2SQL"]
    end
    AGG["📋 Merger node"]
    FA(["✅ Final Answer"])
    UQ --> SUP
    SUP -->|licensing| LA
    SUP -->|onprem| OA
    SUP -->|kb_domain| KA
    LA -.->|results| AGG
    OA -.->|results| AGG
    KA -.->|results| AGG
    AGG --> FA
"""

import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", message=".*ChatVertexAI.*")
warnings.filterwarnings("ignore", message=".*LangChainDeprecationWarning.*")
warnings.filterwarnings("ignore", message=".*allowed_objects.*")

from langchain_core.messages import HumanMessage
from core.graph import build_graph
from core.state import AgentState
from observability.tracer import tracer
from config.settings import settings


def run_query(
    query:      str,
    session_id: str = None,
    user_id:    str = None,
    tags:       list = None,
) -> str:
    """Run a user query through the multi-agent system."""

    app = build_graph()

    initial_state: AgentState = {
        "messages":         [HumanMessage(content=query)],
        "domains":          [],
        "query":            query,
        "domain_responses": {},
        "response":         "",
        "routing_reason":   "",
        "is_multi_domain":  False,
    }

    print(f"\n{'='*60}")
    print(f"📝 Query: {query}")
    print(f"{'='*60}")

    # build_config starts the trace AND returns the invoke config
    config = tracer.build_config(
        query      = query,
        session_id = session_id or settings.session_id,
        user_id    = user_id    or settings.user_id,
        tags       = tags       or ["enterprise-ai", "multi-agent"],
    )

    final_state = app.invoke(initial_state, config=config) if config else app.invoke(initial_state)

    domains   = final_state.get("domains", [])
    reason    = final_state.get("routing_reason", "N/A")
    is_multi  = final_state.get("is_multi_domain", False)
    answer    = final_state["response"]

    print(f"\n{'='*60}")
    print(f"  🧠 Supervisor Decision")
    print(f"{'='*60}")
    if is_multi:
        print(f"  🔀 Multi-domain query!")
        for d in domains:
            print(f"     → {d.upper()} AGENT")
    else:
        print(f"  Domain : {domains[0].upper() if domains else 'UNKNOWN'} AGENT")
    print(f"  Reason : {reason}")
    print(f"\n{'='*60}")
    print(f"  💬 Final Answer")
    print(f"{'='*60}")
    print(answer)
    print(f"{'='*60}\n")

    tracer.flush()
    return answer


if __name__ == "__main__":
    query = input("\n💬 Enter your question: ").strip()
    if query:
        run_query(query)
    print("\n👉 View traces at: https://cloud.langfuse.com")