"""Alembic environment: uses the app's settings and table metadata (no URL or credentials in alembic.ini)."""

from logging.config import fileConfig

from alembic import context

import telecopilot.audit.models  # noqa: F401  (registers the table on Base.metadata)
from telecopilot.config.settings import get_settings
from telecopilot.db.base import Base
from telecopilot.db.session import get_engine

if context.config.config_file_name is not None:
    # Keep loggers that already exist in the calling process (app, tests) enabled.
    fileConfig(context.config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout (`alembic upgrade head --sql`) without connecting."""
    context.configure(url=get_settings().DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
