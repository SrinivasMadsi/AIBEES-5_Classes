"""
scripts/test_mcp.py
Verify the sop-mcp server is reachable and tools work.

Run (with backend dependencies installed):
  poetry run python scripts/test_mcp.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.mcp_client import SOPMCPClient


async def main():
    print("=" * 60)
    print("AI_Onboarding_Platform — MCP Server Sanity Check")
    print("=" * 60)
    print()

    print("→ list_sops()")
    result = await SOPMCPClient.list_sops()
    print(json.dumps(result, indent=2))
    print()

    print("→ extract_rules_for_domain('accumulator')")
    result = await SOPMCPClient.extract_rules_for_domain("accumulator")
    rules = result.get("rules", [])
    print(f"  Got {len(rules)} rules:")
    for r in rules[:5]:
        print(f"    • {r['rule_id']}: {r['rule_name']} [{r['severity']}]")
    if len(rules) > 5:
        print(f"    ... and {len(rules) - 5} more")
    print()

    print("✅ MCP server is working")


if __name__ == "__main__":
    asyncio.run(main())
