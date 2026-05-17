"""
core/mcp_client.py
Client for the sop-mcp server.

Spawns the MCP server as a subprocess and communicates with it via stdio.
This is how the Validation Agent fetches SOPs and rules without ever
touching the filesystem directly.
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config.settings import settings


# Resolve absolute path to the sop-mcp server.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOP_MCP_PATH = PROJECT_ROOT / settings.sop_mcp_server_path


class SOPMCPClient:
    """Async wrapper for sop-mcp tool calls."""

    @staticmethod
    async def _call_tool(tool_name: str, arguments: dict[str, Any]) -> dict:
        """Call a tool on the sop-mcp server and return the parsed result."""
        server_params = StdioServerParameters(
            command="python",
            args=[str(SOP_MCP_PATH)],
            env=None,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                # MCP returns content as a list of TextContent
                if result.content and len(result.content) > 0:
                    text = result.content[0].text
                    return json.loads(text)
                return {}

    @classmethod
    async def list_sops(cls) -> dict:
        """List all available SOPs with metadata."""
        return await cls._call_tool("list_sops", {})

    @classmethod
    async def get_sop_by_domain(cls, domain: str) -> dict:
        """Get full SOP markdown for a domain."""
        return await cls._call_tool("get_sop_by_domain", {"domain": domain})

    @classmethod
    async def extract_rules_for_domain(cls, domain: str) -> dict:
        """Get structured rules for a domain."""
        return await cls._call_tool("extract_rules_for_domain", {"domain": domain})

    @classmethod
    async def search_sop_rules(cls, query: str) -> dict:
        """Free-text search across all SOPs."""
        return await cls._call_tool("search_sop_rules", {"query": query})


# Sync helpers for nodes that don't use async
def list_sops_sync() -> dict:
    return asyncio.run(SOPMCPClient.list_sops())


def get_sop_by_domain_sync(domain: str) -> dict:
    return asyncio.run(SOPMCPClient.get_sop_by_domain(domain))


def extract_rules_for_domain_sync(domain: str) -> dict:
    return asyncio.run(SOPMCPClient.extract_rules_for_domain(domain))
