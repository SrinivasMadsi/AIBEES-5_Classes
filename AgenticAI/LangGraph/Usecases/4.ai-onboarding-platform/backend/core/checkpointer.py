"""
core/checkpointer.py
LangGraph PostgresSaver factory.

Stores agent state in the `public` schema for fault tolerance and resume.
After every node runs, the state is checkpointed — so if the process crashes
mid-validation, you can resume from the last successful node using the same
thread_id.
"""
from functools import lru_cache

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from config.settings import settings


_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    """Lazy-init connection pool for agent state."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.agent_db_url,
            max_size=10,
            kwargs={"autocommit": True, "prepare_threshold": 0},
            open=False,
        )
        _pool.open(wait=True)
    return _pool


@lru_cache(maxsize=1)
def get_checkpointer() -> PostgresSaver:
    """
    Returns the singleton PostgresSaver.
    First call also runs setup() to create checkpoint tables in public schema.
    """
    pool = _get_pool()
    saver = PostgresSaver(pool)
    saver.setup()
    print("[checkpointer] ✅ Checkpoint tables ready")
    return saver
