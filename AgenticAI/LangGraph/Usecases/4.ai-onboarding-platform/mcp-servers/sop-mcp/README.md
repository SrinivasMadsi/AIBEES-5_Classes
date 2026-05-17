# sop-mcp — Model Context Protocol Server for SOPs

This is a standalone MCP server that wraps SOP markdown files and exposes
them through the Model Context Protocol. The AI_Onboarding_Platform backend
talks to this server through MCP — it never reads SOP files directly.

## Why MCP, even for local files?

Even though the SOPs are local markdown files, going through MCP teaches the
**architectural pattern**: the agent depends on a standard protocol, not on
filesystem paths. Tomorrow these SOPs could move to Confluence or SharePoint
without changing a single line of agent code — just swap this server for a
`confluence-mcp` server.

## Tools exposed

| Tool | Purpose |
|---|---|
| `list_sops` | Catalog of available SOPs with metadata |
| `get_sop_by_domain` | Full SOP markdown for a domain |
| `extract_rules_for_domain` | Structured validation rules parsed from a SOP |
| `search_sop_rules` | Free-text search across all SOPs |

## Run

This server runs as a **separate process** from the backend, communicating
over stdio.

```bash
cd mcp-servers/sop-mcp
pip install -e .
python server.py
```

Or use Poetry:

```bash
cd mcp-servers/sop-mcp
poetry install
poetry run python server.py
```

The backend's MCP client (in `backend/core/mcp_client.py`) spawns this
server as a subprocess and communicates with it via stdin/stdout.

## SOP files

| Domain | File | Covers |
|---|---|---|
| `accumulator` | `sops/accumulator.md` | Accumulator sub-section rules |
| `financial` | `sops/financial.md` | Out-of-Pocket, Deductible, Co-pay |
| `clinical` | `sops/clinical.md` | Prior Auth, UM, Care Mgmt, Eligibility |
