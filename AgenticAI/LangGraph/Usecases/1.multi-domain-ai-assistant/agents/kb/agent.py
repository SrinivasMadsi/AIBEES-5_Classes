"""
agents/kb/agent.py
KB domain agent — fully self-contained.
"""

from agents.base_agent import BaseDomainAgent
from agents.kb.tools import KB_TOOLS
from agents.kb.prompts import KB_PROMPT
from core.state import AgentState


class KBAgent(BaseDomainAgent):
    """Knowledge Base domain expert agent."""

    @property
    def tools(self) -> list:
        return KB_TOOLS

    @property
    def prompt(self) -> str:
        return KB_PROMPT

    @property
    def domain(self) -> str:
        return "kb_domain"

    @property
    def icon(self) -> str:
        return "📚"


_agent = KBAgent()


def kb_agent_node(state: AgentState) -> AgentState:
    """LangGraph node function — thin wrapper around the agent."""
    return _agent.as_node(state)
