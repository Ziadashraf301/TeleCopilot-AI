import math
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from telecopilot.config.settings import get_settings


def _connect_args(database_url: str, timeout_s: float) -> dict:
    # psycopg takes a whole-second connect timeout; SQLite (tests) has no network connect step.
    if make_url(database_url).get_backend_name() == "postgresql":
        return {"connect_timeout": math.ceil(timeout_s)}
    return {}


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """One connection pool per process. Lives here, not in core.singletons, because core must not import db."""
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # drop connections Postgres closed (restart, idle timeout) instead of failing a request
        connect_args=_connect_args(settings.DATABASE_URL, settings.DB_TIMEOUT_S),
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request. Services commit explicitly; anything uncommitted rolls back."""
    with get_session_factory()() as session:
        yield session
