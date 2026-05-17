"""
core/db.py
SQLAlchemy engine and session factory for the business_data schema.

Uses an event listener to SET search_path on every connection — works on
both Neon pooled and unpooled endpoints (Neon pooled mode rejects search_path
in the connection-string options parameter).
"""
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings


def _make_engine() -> Engine:
    """Create SQLAlchemy engine with production-quality pool settings."""
    engine = create_engine(
        settings.business_db_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_search_path(dbapi_conn, _conn_record):
        """Set search_path to business_data on every new connection."""
        cursor = dbapi_conn.cursor()
        cursor.execute("SET search_path TO business_data, public")
        cursor.close()

    return engine


engine: Engine = _make_engine()
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager yielding a SQLAlchemy session with auto-commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def healthcheck() -> bool:
    """Returns True if the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
