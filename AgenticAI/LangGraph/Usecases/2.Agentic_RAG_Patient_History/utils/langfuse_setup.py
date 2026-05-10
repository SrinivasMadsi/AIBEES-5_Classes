"""
utils/langfuse_setup.py
"""

import logging, os

os.environ["OTEL_LOG_LEVEL"]  = "error"
os.environ["LANGFUSE_DEBUG"]  = "False"

for _n in ["langfuse", "opentelemetry", "urllib3", "google.ai"]:
    _l = logging.getLogger(_n)
    _l.setLevel(logging.ERROR)
    _l.propagate = False

logging.basicConfig(level=logging.INFO)

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler


def init_langfuse():
    langfuse = Langfuse()
    ok = langfuse.auth_check()
    print(f"Langfuse connected: {ok}")
    if not ok:
        print("  Check LANGFUSE_PUBLIC_KEY / SECRET_KEY in .env")
    # Create one shared handler — session/user set via env or Langfuse dashboard
    handler = CallbackHandler()
    return langfuse, handler


def make_config(_handler, run_name: str, tags: list, user_id: str = "doctor") -> dict:
    """
    Builds a LangGraph invoke config with Langfuse callbacks.
    Uses a fresh CallbackHandler per call to avoid cross-trace contamination.
    """
    handler = CallbackHandler()
    return {
        "callbacks": [handler],
        "run_name":  run_name,
    }


def flush_traces(langfuse_client) -> None:
    try:
        langfuse_client.flush()
        print("Traces flushed → https://cloud.langfuse.com")
    except Exception as e:
        print(f"Flush warning: {e}")