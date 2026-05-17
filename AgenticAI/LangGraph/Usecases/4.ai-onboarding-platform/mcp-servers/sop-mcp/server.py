"""
sop-mcp / server.py
─────────────────────────────────────────────────────────────────────────────
MCP server exposing SOP (Standard Operating Procedure) documents.

This server demonstrates the MCP pattern: it wraps a folder of markdown
files and exposes them through the Model Context Protocol. The agent
backend never reads files directly — it talks to this server via MCP.

Tools exposed:
  • list_sops              — catalog of available SOPs
  • get_sop_by_domain      — full SOP markdown for a domain
  • extract_rules_for_domain — structured rules parsed from a SOP
  • search_sop_rules       — free-text search across all SOPs

Run as:
  python server.py
"""
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# ── Configuration ───────────────────────────────────────────────────────────
SOPS_DIR = Path(__file__).resolve().parent / "sops"

# Map domain names to SOP files
DOMAIN_TO_FILE = {
    "accumulator": "accumulator.md",
    "financial":   "financial.md",
    "clinical":    "clinical.md",
}

# ── MCP Server ──────────────────────────────────────────────────────────────
server = Server("sop-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Tool discovery — what can this server do?"""
    return [
        Tool(
            name="list_sops",
            description="List all available SOP documents with metadata",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_sop_by_domain",
            description=(
                "Get the full SOP markdown content for a specific domain. "
                "Valid domains: accumulator, financial, clinical."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "SOP domain identifier",
                        "enum": list(DOMAIN_TO_FILE.keys()),
                    },
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="extract_rules_for_domain",
            description=(
                "Extract structured validation rules from the SOP for a "
                "given domain. Returns a list of rules with id, name, "
                "severity, affected fields, and suggested fixes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "enum": list(DOMAIN_TO_FILE.keys()),
                    },
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="search_sop_rules",
            description="Free-text search across all SOPs for relevant rules",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (matches rule names, fields, descriptions)",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Tool invocation — dispatch to the right handler."""
    if name == "list_sops":
        result = _list_sops()
    elif name == "get_sop_by_domain":
        result = _get_sop_by_domain(arguments["domain"])
    elif name == "extract_rules_for_domain":
        result = _extract_rules_for_domain(arguments["domain"])
    elif name == "search_sop_rules":
        result = _search_sop_rules(arguments["query"])
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ── Tool implementations ────────────────────────────────────────────────────

def _list_sops() -> dict:
    """Return catalog of available SOPs with metadata."""
    sops = []
    for domain, filename in DOMAIN_TO_FILE.items():
        path = SOPS_DIR / filename
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        # Extract metadata from frontmatter-like markdown header
        metadata = _extract_metadata(content)
        sops.append({
            "domain": domain,
            "filename": filename,
            "document_id": metadata.get("Document ID", "unknown"),
            "version": metadata.get("Version", "unknown"),
            "last_reviewed": metadata.get("Last Reviewed", "unknown"),
            "owner": metadata.get("Owner", "unknown"),
        })
    return {"sops": sops, "total": len(sops)}


def _get_sop_by_domain(domain: str) -> dict:
    """Return full markdown content for a domain's SOP."""
    filename = DOMAIN_TO_FILE.get(domain)
    if not filename:
        return {"error": f"Unknown domain: {domain}"}

    path = SOPS_DIR / filename
    if not path.exists():
        return {"error": f"SOP file not found: {filename}"}

    return {
        "domain": domain,
        "filename": filename,
        "content": path.read_text(encoding="utf-8"),
    }


def _extract_rules_for_domain(domain: str) -> dict:
    """Parse SOP markdown into structured validation rules."""
    filename = DOMAIN_TO_FILE.get(domain)
    if not filename:
        return {"error": f"Unknown domain: {domain}"}

    path = SOPS_DIR / filename
    if not path.exists():
        return {"error": f"SOP file not found: {filename}"}

    content = path.read_text(encoding="utf-8")
    rules = _parse_rules_from_markdown(content, domain)

    return {
        "domain": domain,
        "filename": filename,
        "rules": rules,
        "total_rules": len(rules),
    }


def _search_sop_rules(query: str) -> dict:
    """Free-text search across all SOPs."""
    query_lower = query.lower()
    matches = []

    for domain, filename in DOMAIN_TO_FILE.items():
        path = SOPS_DIR / filename
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8")
        rules = _parse_rules_from_markdown(content, domain)

        for rule in rules:
            haystack = " ".join([
                rule.get("rule_id", ""),
                rule.get("rule_name", ""),
                rule.get("description", ""),
            ]).lower()

            if query_lower in haystack:
                matches.append({
                    "domain": domain,
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "snippet": rule.get("description", "")[:200],
                })

    return {"query": query, "matches": matches, "total": len(matches)}


# ── Parsing helpers ─────────────────────────────────────────────────────────

def _extract_metadata(content: str) -> dict:
    """Extract bold-prefixed metadata lines from markdown header."""
    metadata = {}
    for line in content.split("\n")[:20]:  # Header is in first 20 lines
        match = re.match(r"\*\*([^:]+):\*\*\s*(.+)", line)
        if match:
            metadata[match.group(1).strip()] = match.group(2).strip()
    return metadata


def _parse_rules_from_markdown(content: str, domain: str) -> list[dict]:
    """
    Parse markdown SOP into structured rules.

    Rule sections look like:
      ### Rule ACC-01 — Accumulator activation requires contract year
      **Severity:** fail_fixable
      **Field:** 122 (contract year start date)
      <description>
    """
    rules = []

    # Split by H3 rule headers
    rule_pattern = r"### Rule ([A-Z]+-\d+)\s*[—–-]\s*(.+?)\n(.+?)(?=\n###|\Z)"
    matches = re.findall(rule_pattern, content, re.DOTALL)

    for rule_id, rule_name, body in matches:
        rule = {
            "rule_id": rule_id.strip(),
            "rule_name": rule_name.strip(),
            "domain": domain,
            "severity": _extract_field(body, "Severity"),
            "affected_fields": _extract_fields(body),
            "description": _extract_description(body),
            "formula": _extract_field(body, "Formula"),
            "suggested_fix": _extract_field(body, "Suggested fix"),
            "auto_fixable": "Auto-fix.*NOT permitted" not in body,
        }
        rules.append(rule)

    return rules


def _extract_field(body: str, key: str) -> str | None:
    """Extract value of a **Key:** value pattern."""
    match = re.search(rf"\*\*{re.escape(key)}:\*\*\s*([^\n]+)", body)
    return match.group(1).strip() if match else None


def _extract_fields(body: str) -> list[str]:
    """Extract field references like 'Field: 122' or 'Fields: 141, 142'."""
    # Singular
    match = re.search(r"\*\*Field:\*\*\s*(\d+)", body)
    if match:
        return [match.group(1)]
    # Plural
    match = re.search(r"\*\*Fields:\*\*\s*([^\n]+)", body)
    if match:
        return re.findall(r"\d+", match.group(1))
    return []


def _extract_description(body: str) -> str:
    """Extract the human-readable description (everything after the metadata bullets)."""
    # Skip the **Severity** / **Field** lines, grab the paragraph after
    lines = body.split("\n")
    desc_lines = []
    started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("**") and stripped.endswith("**"):
            continue
        if not stripped:
            if started:
                break
            continue
        if not stripped.startswith("**"):
            started = True
            desc_lines.append(stripped)
    return " ".join(desc_lines[:3])  # First 3 lines of description


# ── Entry point ─────────────────────────────────────────────────────────────

async def main():
    """Run the MCP server over stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
