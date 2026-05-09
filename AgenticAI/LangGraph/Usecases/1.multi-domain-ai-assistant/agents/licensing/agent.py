"""
agents/licensing/agent.py
Licensing domain agent — fully self-contained.

This file only knows about:
  - Its own tools (from agents/licensing/tools.py)
  - Its own prompt (from agents/licensing/prompts.py)
  - The base agent interface (from agents/base_agent.py)

It does NOT import from onprem or kb agents.
It does NOT know about the graph, supervisor, or merger.
"""

from agents.base_agent import BaseDomainAgent
from agents.licensing.tools import LICENSING_TOOLS
from agents.licensing.prompts import LICENSING_PROMPT
from core.state import AgentState


class LicensingAgent(BaseDomainAgent):
    """Licensing domain expert agent."""

    @property
    def tools(self) -> list:
        return LICENSING_TOOLS

    @property
    def prompt(self) -> str:
        return LICENSING_PROMPT

    @property
    def domain(self) -> str:
        return "licensing"

    @property
    def icon(self) -> str:
        return "🔑"


# ── Singleton instance ────────────────────────────────────────────────────────
_agent = LicensingAgent()


def licensing_agent_node(state: AgentState) -> AgentState:
    """LangGraph node function — thin wrapper around the agent."""
    return _agent.as_node(state)
