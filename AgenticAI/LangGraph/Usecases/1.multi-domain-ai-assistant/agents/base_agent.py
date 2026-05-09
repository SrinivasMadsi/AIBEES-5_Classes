"""
agents/base_agent.py
Abstract base agent — all domain agents inherit from this.

KEY FIX: The run() method now picks up the shared Langfuse callback
from the tracer singleton, so nested ReAct agent calls appear
inside the same Langfuse trace as the parent graph execution.
"""

from abc import ABC, abstractmethod
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from core.llm import get_llm
from core.state import AgentState


class BaseDomainAgent(ABC):
    """
    Abstract base for all domain agents.

    Subclasses must implement:
        - tools     : list of LangChain tools scoped to this domain
        - prompt    : system prompt string for this domain
        - domain    : domain name string
        - icon      : emoji for terminal output
    """

    @property
    @abstractmethod
    def tools(self) -> list:
        """Domain-scoped tools — only this domain's data sources."""
        ...

    @property
    @abstractmethod
    def prompt(self) -> str:
        """System prompt — domain expertise and tool instructions."""
        ...

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain name: licensing / onprem / kb_domain."""
        ...

    @property
    @abstractmethod
    def icon(self) -> str:
        """Terminal display icon."""
        ...

    def run(self, query: str) -> str:
        """
        Execute the domain agent against a query.
        Picks up the shared Langfuse callback from tracer so all
        tool calls and LLM invocations appear in the same trace.
        """
        # Import here to avoid circular imports
        from observability.tracer import tracer

        llm   = get_llm(temperature=0.1)
        agent = create_react_agent(
            model  = llm,
            tools  = self.tools,
            prompt = self.prompt,
        )

        # Pass shared Langfuse callbacks into nested agent
        # This connects tool calls and LLM calls to the parent trace
        callbacks = tracer.get_callbacks()
        config    = {"callbacks": callbacks} if callbacks else {}

        result   = agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config,
        )
        messages = result.get("messages", [])

        # Extract last AIMessage content
        for msg in reversed(messages):
            if not isinstance(msg, AIMessage):
                continue
            content = msg.content

            # Plain string response
            if isinstance(content, str) and content.strip():
                return content.strip()

            # Gemini list-of-blocks format
            if isinstance(content, list):
                texts = [
                    b.get("text", "").strip()
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                joined = "\n".join(t for t in texts if t)
                if joined:
                    return joined

        return "No response generated."

    def as_node(self, state: AgentState) -> AgentState:
        """
        LangGraph node wrapper — runs the agent and stores response in state.
        Each domain agent stores its response under its domain key.
        """
        print(f"\n{self.icon}  [{self.domain.upper()} Agent] Processing query...")
        response = self.run(state["query"])
        print(f"  ✅ {self.domain.upper()} agent response ready.")

        updated = dict(state.get("domain_responses", {}))
        updated[self.domain] = response
        return {**state, "domain_responses": updated}