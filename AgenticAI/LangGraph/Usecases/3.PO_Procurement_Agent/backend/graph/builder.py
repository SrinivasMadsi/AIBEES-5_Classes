"""
graph/builder.py
Wires the Composer + Auditor + self-correction into a single LangGraph.

Flow:
  start → intake → enrichment → vendor_mapping → tax_calc → assembler
        → inventory_check → price_check → policy_check → schema_check
        → critic
        ├── verdict == PASS / PASS_WITH_WARNINGS / FAIL_REJECT → finalize → end
        └── verdict == FAIL_FIXABLE and iteration < max → self_correction
              → tax_calc (loop back; reuses the rest of the audit pipeline)

Visualization (auto-generated on every graph build):
  - backend/graph/po_agent_graph.mmd  — Mermaid source (renders in GitHub, VS Code)
  - backend/graph/po_agent_graph.png  — PNG image (double-click to view)

The PNG is rendered via mermaid.ink (public API, needs internet).
If PNG rendering fails, the .mmd file is still produced and the agent
runs normally — visualization is non-essential to graph execution.
"""
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from agents.composer import (
    assembler_node,
    enrichment_node,
    intake_node,
    tax_calc_node,
    vendor_mapping_node,
)
from agents.auditor import (
    critic_node,
    inventory_check_node,
    policy_check_node,
    price_check_node,
    schema_check_node,
)
from core.checkpointer import get_checkpointer
from graph.self_correction import finalize_node, self_correction_node
from graph.state import POState

# ── Paths for auto-generated visualization ───────────────────────────────────
_GRAPH_DIR = Path(__file__).resolve().parent
_MMD_PATH  = _GRAPH_DIR / "po_agent_graph.mmd"
_PNG_PATH  = _GRAPH_DIR / "po_agent_graph.png"


def _route_after_critic(state: POState) -> str:
    """Decide whether to self-correct, loop is exhausted, or finalize."""
    verdict = state.get("verdict", "")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 1)

    if verdict == "FAIL_FIXABLE" and iteration < max_iter:
        return "self_correction"
    return "finalize"


def _save_visualizations(graph) -> None:
    """
    Save both Mermaid source (.mmd) and PNG image (.png) of the compiled graph.

    Both files are saved in graph/ folder next to this builder. Runs on every
    graph build. Failures are non-fatal — visualization is a debugging aid,
    not a runtime dependency.
    """
    # 1. Mermaid source — pure text, never fails (no network)
    try:
        mermaid_source = graph.get_graph().draw_mermaid()
        _MMD_PATH.write_text(mermaid_source, encoding="utf-8")
        print(f"[graph] 📊 Mermaid diagram saved → {_MMD_PATH.name}")
    except Exception as e:
        print(f"[graph] ⚠️  Mermaid generation skipped: {e}")
        return  # If .mmd failed, .png will fail too

    # 2. PNG image — uses mermaid.ink public API (needs internet)
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        _PNG_PATH.write_bytes(png_bytes)
        print(f"[graph] 🖼️  PNG diagram saved    → {_PNG_PATH.name}")
    except Exception as e:
        # Common reasons: no internet, mermaid.ink rate limit, firewall block
        print(f"[graph] ⚠️  PNG generation skipped: {e}")
        print(f"[graph]     (open {_MMD_PATH.name} in VS Code or paste into mermaid.live)")


def build_graph(use_checkpointer: bool = True, save_diagram: bool = True):
    """Compile the PO agent graph.

    Args:
        use_checkpointer: When True, attach the Postgres checkpointer for fault
            tolerance. Set False for visualization or unit tests.
        save_diagram: When True, write Mermaid + PNG diagrams to graph/ folder
            after compiling. Default True so the diagrams stay in sync with code.
    """
    builder = StateGraph(POState)

    # Composer nodes
    builder.add_node("intake",         intake_node)
    builder.add_node("enrichment",     enrichment_node)
    builder.add_node("vendor_mapping", vendor_mapping_node)
    builder.add_node("tax_calc",       tax_calc_node)
    builder.add_node("assembler",      assembler_node)

    # Auditor nodes
    builder.add_node("inventory_check", inventory_check_node)
    builder.add_node("price_check",     price_check_node)
    builder.add_node("policy_check",    policy_check_node)
    builder.add_node("schema_check",    schema_check_node)
    builder.add_node("critic",          critic_node)

    # Self-correction + finalize
    builder.add_node("self_correction", self_correction_node)
    builder.add_node("finalize",        finalize_node)

    # ── Composer pipeline ────────────────────────────────────────────────────
    builder.add_edge(START,            "intake")
    builder.add_edge("intake",         "enrichment")
    builder.add_edge("enrichment",     "vendor_mapping")
    builder.add_edge("vendor_mapping", "tax_calc")
    builder.add_edge("tax_calc",       "assembler")

    # ── Auditor pipeline ─────────────────────────────────────────────────────
    builder.add_edge("assembler",       "inventory_check")
    builder.add_edge("inventory_check", "price_check")
    builder.add_edge("price_check",     "policy_check")
    builder.add_edge("policy_check",    "schema_check")
    builder.add_edge("schema_check",    "critic")

    # ── Branch: loop back or finalize ────────────────────────────────────────
    builder.add_conditional_edges(
        "critic",
        _route_after_critic,
        {"self_correction": "self_correction", "finalize": "finalize"},
    )

    # Self-correction loops back to tax_calc (so tax recomputes after price/qty changes)
    builder.add_edge("self_correction", "tax_calc")
    builder.add_edge("finalize", END)

    if use_checkpointer:
        graph = builder.compile(checkpointer=get_checkpointer())
    else:
        graph = builder.compile()

    if save_diagram:
        _save_visualizations(graph)

    return graph


# Singleton graph instance — built once at import
_graph = None


def get_graph(use_checkpointer: bool = True):
    """Return the singleton compiled graph."""
    global _graph
    if _graph is None:
        _graph = build_graph(use_checkpointer=use_checkpointer)
    return _graph