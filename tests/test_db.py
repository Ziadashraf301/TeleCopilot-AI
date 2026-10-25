"""Postgres plumbing, tested on SQLite so CI needs no database server."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select

from telecopilot.audit.models import AuditLog
from telecopilot.config.settings import get_settings
from telecopilot.db.session import get_db_session, get_engine, get_session_factory

ALEMBIC_INI = Path(__file__).parents[1] / "alembic.ini"


def clear_cached_clients() -> None:
    for cached in (get_settings, get_engine, get_session_factory):
        cached.cache_clear()


@pytest.fixture
def alembic_config(tmp_path, monkeypatch) -> Config:
    """Point the app (and Alembic, which reads the app settings) at a throwaway SQLite file."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}")
    clear_cached_clients()
    yield Config(str(ALEMBIC_INI))
    get_engine().dispose()
    clear_cached_clients()


@pytest.fixture
def migrated_db(alembic_config):
    command.upgrade(alembic_config, "head")
    return alembic_config


def open_session():
    return next(get_db_session())


def test_migrations_upgrade_and_downgrade(alembic_config):
    command.upgrade(alembic_config, "head")
    assert "audit_log" in inspect(get_engine()).get_table_names()

    command.downgrade(alembic_config, "base")
    assert "audit_log" not in inspect(get_engine()).get_table_names()


def test_models_match_latest_migration(migrated_db):
    command.check(migrated_db)  # raises if a model changed without a migration


def test_audit_log_round_trip(migrated_db):
    session = open_session()
    session.add(AuditLog(actor="system", action="ingest.run", entity_type="source", details={"note": "تحديث الباقات"}))
    session.commit()
    session.close()

    row = open_session().scalars(select(AuditLog)).one()
    assert (row.id, row.actor, row.action, row.entity_type, row.entity_id) == (
        1,
        "system",
        "ingest.run",
        "source",
        None,
    )
    assert row.details == {"note": "تحديث الباقات"}
    assert row.occurred_at is not None  # filled by the database default


def test_uncommitted_changes_roll_back_when_the_session_closes(migrated_db):
    sessions = get_db_session()
    session = next(sessions)
    session.add(AuditLog(actor="system", action="never.committed"))
    session.flush()
    sessions.close()  # what FastAPI does after the request

    assert open_session().scalar(select(func.count()).select_from(AuditLog)) == 0
