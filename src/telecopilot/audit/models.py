from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from telecopilot.db.base import Base

# BIGINT identity on Postgres; SQLite (tests) only auto-increments a plain INTEGER primary key.
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")
# JSONB on Postgres (indexable, compact); plain JSON elsewhere.
JsonDocument = JSON().with_variant(JSONB(), "postgresql")
SHORT_TEXT = 64


class AuditLog(Base):
    """Append-only record of who did what to which entity. Who writes which actions is decided in the M1 ERD."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor: Mapped[str] = mapped_column(String(SHORT_TEXT))  # CSR id, or "system" until auth exists (M1)
    action: Mapped[str] = mapped_column(String(SHORT_TEXT))  # e.g. "ingest.run", "ticket.update"
    entity_type: Mapped[str | None] = mapped_column(String(SHORT_TEXT))
    entity_id: Mapped[str | None] = mapped_column(String(SHORT_TEXT))
    details: Mapped[dict[str, Any]] = mapped_column(JsonDocument, default=dict)
