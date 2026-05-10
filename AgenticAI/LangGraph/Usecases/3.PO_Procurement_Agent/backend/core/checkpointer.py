"""
core/checkpointer.py
LangGraph PostgresSaver factory.

Stores agent state in the `public` schema. LangGraph's checkpoint tables have
distinctive names (`checkpoints`, `checkpoint_writes`, etc.) so they don't
conflict with business tables (which live in `business_data`).
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
    First call also runs setup() to verify the checkpoint tables exist
    (they were created when this was first run).
    """
    pool = _get_pool()
    saver = PostgresSaver(pool)
    saver.setup()
    print("[checkpointer] ✅ Checkpoint tables ready")
    return saver