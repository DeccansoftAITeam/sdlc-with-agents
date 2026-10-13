"""TD-008 tables. All tenant-owned with forced RLS (migration td008a)."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TenantOwned

_TICKET_FK = (["tenant_id", "ticket_id"], ["tickets.tenant_id", "tickets.id"])


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )


class TriageJob(TenantOwned, Base):
    __tablename__ = "ai_triage_jobs"
    __table_args__ = (
        ForeignKeyConstraint(*_TICKET_FK, ondelete="CASCADE"),
        CheckConstraint("status IN ('queued', 'paused', 'done', 'failed')", name="ck_ai_triage_jobs_status"),
        Index("ix_ai_triage_jobs_queued", "created_at", postgresql_where=text("status = 'queued'")),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(Text, server_default=text("'queued'"))
    attempts: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    paused_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class Suggestion(TenantOwned, Base):
    __tablename__ = "ai_suggestions"
    __table_args__ = (
        ForeignKeyConstraint(*_TICKET_FK, ondelete="CASCADE"),
        UniqueConstraint("tenant_id", "ticket_id", name="uq_ai_suggestions_ticket"),
        CheckConstraint(
            "decision IN ('pending', 'accepted', 'overridden')", name="ck_ai_suggestions_decision"
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    category: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(Text, server_default=text("'pending'"))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))


class Usage(TenantOwned, Base):
    """Monthly AI usage per tenant: the ledger behind the 200k-token cap (ADR-0004)."""

    __tablename__ = "ai_usage"
    __table_args__ = (PrimaryKeyConstraint("tenant_id", "month", name="pk_ai_usage"),)

    month: Mapped[date] = mapped_column(Date)  # first day of the month (UTC)
    input_tokens: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    output_tokens: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    requests: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
