"""
core/tracer.py
Langfuse v3 wrapper for observability.

When LANGFUSE_ENABLED=true, every LLM call, node, and MCP call is traced
to Langfuse Cloud as a hierarchical span tree.
"""
from typing import Any

from config.settings import settings

_langfuse_client = None
_callback_handler = None


def _get_langfuse():
    """Lazy-init Langfuse client. Returns None if disabled."""
    global _langfuse_client
    if not settings.langfuse_enabled:
        return None
    if _langfuse_client is not None:
        return _langfuse_client

    try:
        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )

        # Verify auth
        ok = _langfuse_client.auth_check()
        if ok:
            print("🔍 Langfuse Auth: ✅ Connected")
        else:
            print("🔍 Langfuse Auth: ❌ Failed (check keys)")
            _langfuse_client = None
    except ImportError:
        print("⚠️  Langfuse not installed — set LANGFUSE_ENABLED=false")
        return None
    except Exception as e:
        print(f"⚠️  Langfuse init error: {e}")
        return None

    return _langfuse_client


def _get_callback_handler():
    """Lazy-init Langfuse callback handler for LangChain/LangGraph."""
    global _callback_handler
    if not settings.langfuse_enabled:
        return None
    if _callback_handler is not None:
        return _callback_handler

    try:
        from langfuse.langchain import CallbackHandler
        _callback_handler = CallbackHandler()
    except Exception as e:
        print(f"⚠️  Langfuse callback init error: {e}")
        return None

    return _callback_handler


def build_config(
    run_name: str = "ai_onboarding",
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build a LangGraph config dict with Langfuse callbacks attached.

    Usage:
        config = build_config(session_id=thread_id, user_id="ipm@example.com")
        graph.invoke(state, config={**graph_config, **config})
    """
    handler = _get_callback_handler()
    if handler is None:
        return {}

    return {
        "callbacks": [handler],
        "run_name": run_name,
        "metadata": {
            "langfuse_session_id": session_id or "default",
            "langfuse_user_id": user_id or "anonymous",
            "langfuse_tags": tags or ["ai-onboarding"],
        },
    }


def flush() -> None:
    """Force Langfuse to flush pending traces."""
    client = _get_langfuse()
    if client is not None:
        try:
            client.flush()
        except Exception as e:
            print(f"⚠️  Langfuse flush error: {e}")


# Trigger init on import (prints status message)
_get_langfuse()
