"""
observability/tracer.py
Langfuse observability for the Enterprise AI multi-agent system.

Provides a singleton Tracer that attaches Langfuse callbacks to LangGraph
invocations so all supervisor, domain agent, tool, and merger calls are
captured under a single trace per query, with proper parent-child nesting.
"""

import os
import logging
from config.settings import settings

logger = logging.getLogger("enterprise_ai.observability")

# ── Silence noisy logs from telemetry libraries ───────────────────────────────
os.environ["OTEL_LOG_LEVEL"] = "error"
os.environ["LANGFUSE_DEBUG"] = "False"

for _name in ["langfuse", "opentelemetry", "opentelemetry.attributes","opentelemetry.sdk", "urllib3", "google.ai"]:
    _log = logging.getLogger(_name)
    _log.setLevel(logging.ERROR)
    _log.propagate = False


class Tracer:
    """
    Wrapper around the Langfuse client and LangChain callback handler.

    Exposes a small surface used by the rest of the application:
      - build_config(): returns the config dict to pass into graph.invoke()
      - get_callbacks(): returns the callback list for nested agent invocations
      - flush(): pushes pending traces to Langfuse cloud before shutdown
    """

    def __init__(self):
        """
        Initialize the Langfuse client and a reusable callback handler.

        Reads credentials from environment variables (LANGFUSE_PUBLIC_KEY,
        LANGFUSE_SECRET_KEY, LANGFUSE_HOST). If Langfuse is disabled in
        settings or initialization fails, the tracer silently degrades:
        build_config() returns an empty dict and no traces are sent.
        """
        self._enabled    = settings.langfuse_enabled
        self._lf         = None
        self._get_client = None
        self._handler    = None

        if not self._enabled:
            return

        try:
            from langfuse import Langfuse, get_client
            from langfuse.langchain import CallbackHandler

            self._lf          = Langfuse()
            self._get_client  = get_client
            self._handler     = CallbackHandler()

            ok = self._lf.auth_check()
            print(f"🔍 Langfuse Auth: {'✅ Connected' if ok else '❌ Failed'}")
        except Exception as e:
            print(f"⚠️  Langfuse not available: {e}")
            self._enabled = False

    def build_config(self, query: str, session_id: str, user_id: str, tags: list) -> dict:
        """
        Build the config dict for a LangGraph invocation.

        The returned dict attaches the Langfuse callback handler and embeds
        session_id, user_id, and tags as metadata so they appear on the
        resulting trace in the Langfuse UI. Pass the return value directly
        into graph.invoke(state, config=...).

        Parameters
        ----------
        query : str
            The user query — used to construct a human-readable run_name.
        session_id : str
            Logical session identifier; groups related traces together.
        user_id : str
            Identifier of the end user issuing the query.
        tags : list
            List of string tags for filtering and searching traces.

        Returns
        -------
        dict
            A LangGraph config dict, or an empty dict if tracing is disabled.
        """
        if not self._enabled or not self._handler:
            return {}

        return {
            "callbacks": [self._handler],
            "run_name":  f"enterprise-ai | {query[:60]}",
            "metadata": {
                "langfuse_session_id": session_id,
                "langfuse_user_id":    user_id,
                "langfuse_tags":       tags or [],
                "system":              "Enterprise AI Multi-Agent",
                "version":             "v2",
            },
        }

    def get_callbacks(self) -> list:
        """
        Return the callback list to attach to nested agent invocations.

        Domain agents call this to ensure their internal LLM and tool calls
        nest under the same parent trace created by the top-level graph
        invocation, preserving the full execution tree in Langfuse.

        Returns
        -------
        list
            A list containing the shared CallbackHandler, or an empty list
            if tracing is disabled.
        """
        if not self._enabled or not self._handler:
            return []
        return [self._handler]

    def flush(self):
        """
        Push all pending traces to Langfuse cloud.

        Should be called once before the application exits or at the end of
        a request lifecycle to guarantee traces are not lost. Failures are
        logged and swallowed so they never break the main flow.
        """
        if not self._enabled:
            return
        try:
            self._get_client().flush()
            print("📡 Trace flushed to Langfuse!")
        except Exception as e:
            logger.warning("Langfuse flush failed: %s", e)


# ── Singleton ─────────────────────────────────────────────────────────────────
tracer = Tracer()