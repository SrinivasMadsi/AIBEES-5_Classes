"""
agents/onprem/agent.py
OnPrem domain agent — fully self-contained.
"""

from agents.base_agent import BaseDomainAgent
from agents.onprem.tools import ONPREM_TOOLS
from agents.onprem.prompts import ONPREM_PROMPT
from core.state import AgentState


class OnPremAgent(BaseDomainAgent):
    """OnPrem infrastructure domain expert agent."""

    @property
    def tools(self) -> list:
        return ONPREM_TOOLS

    @property
    def prompt(self) -> str:
        return ONPREM_PROMPT

    @property
    def domain(self) -> str:
        return "onprem"

    @property
    def icon(self) -> str:
        return "🖥️"


_agent = OnPremAgent()


def onprem_agent_node(state: AgentState) -> AgentState:
    """LangGraph node function — thin wrapper around the agent."""
    return _agent.as_node(state)
