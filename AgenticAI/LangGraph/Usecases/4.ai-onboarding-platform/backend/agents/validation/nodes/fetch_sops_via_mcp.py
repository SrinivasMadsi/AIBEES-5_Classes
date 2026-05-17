"""
agents/validation/nodes/fetch_sops_via_mcp.py
Node: fetch_sops_via_mcp

This is THE node that demonstrates MCP. It calls the sop-mcp server (a
separate process) via the Model Context Protocol to retrieve SOPs.

The agent NEVER reads SOP files directly. All access goes through the
MCP server. This is the key architectural pattern of MCP.
"""
from core.mcp_client import SOPMCPClient
from graph.state import MainState
import asyncio


def fetch_sops_via_mcp_node(state: MainState) -> dict:
    """Call sop-mcp server to fetch structured rules for each domain."""
    domain_groups = state.get("domain_groups", {})

    print(f"[validation.fetch_sops_via_mcp] 🔌 calling sop-mcp server for {len(domain_groups)} domain(s)...")

    sop_rules_by_domain: dict[str, list] = {}

    async def _fetch_all():
        for domain in domain_groups.keys():
            result = await SOPMCPClient.extract_rules_for_domain(domain)
            rules = result.get("rules", [])
            sop_rules_by_domain[domain] = rules
            print(f"    🔌 [{domain}] received {len(rules)} rule(s) from sop-mcp")

    asyncio.run(_fetch_all())

    total_rules = sum(len(r) for r in sop_rules_by_domain.values())
    print(f"[validation.fetch_sops_via_mcp] ✅ fetched {total_rules} total rule(s) via MCP")

    return {"sop_rules_by_domain": sop_rules_by_domain}
