"""
core/tracer.py
Langfuse v3 observability wrapper.
"""
import logging
import os

from config.settings import settings

logger = logging.getLogger(__name__)

# Silence noisy logs from telemetry libraries
os.environ["OTEL_LOG_LEVEL"] = "error"
os.environ["LANGFUSE_DEBUG"] = "False"

for _name in ["langfuse", "opentelemetry", "opentelemetry.attributes",
              "opentelemetry.sdk", "urllib3", "google.ai"]:
    _log = logging.getLogger(_name)
    _log.setLevel(logging.ERROR)
    _log.propagate = False


class Tracer:
    """Wrapper around the Langfuse v3 client and LangChain callback handler."""

    def __init__(self):
        self._enabled = settings.langfuse_enabled
        self._lf = None
        self._get_client = None
        self._handler = None

        if not self._enabled:
            return

        try:
            from langfuse import Langfuse, get_client
            from langfuse.langchain import CallbackHandler

            self._lf = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            self._get_client = get_client
            self._handler = CallbackHandler()

            ok = self._lf.auth_check()
            print(f"🔍 Langfuse Auth: {'✅ Connected' if ok else '❌ Failed'}")
        except Exception as e:
            print(f"⚠️  Langfuse not available: {e}")
            self._enabled = False

    def build_config(self, run_name: str, session_id: str, user_id: str = "anonymous",
                     tags: list | None = None) -> dict:
        """Build a LangGraph config with Langfuse callback and metadata."""
        if not self._enabled or not self._handler:
            return {}

        return {
            "callbacks": [self._handler],
            "run_name": run_name,
            "metadata": {
                "langfuse_session_id": session_id,
                "langfuse_user_id": user_id,
                "langfuse_tags": tags or [],
                "system": "po-agent",
                "version": "v1",
            },
        }

    def flush(self):
        """Flush all pending traces."""
        if not self._enabled:
            return
        try:
            self._get_client().flush()
        except Exception as e:
            logger.warning("Langfuse flush failed: %s", e)


tracer = Tracer()
