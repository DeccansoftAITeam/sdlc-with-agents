"""Tickets and messages (TD-003, TD-004). Tenant-owned with forced RLS (migration td003a).

Composite foreign keys (tenant_id, …) make the database refuse cross-tenant references,
even if application code is wrong (same pattern as TD-001).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TenantOwned, Timestamped

STATUSES = ("new", "open", "pending_customer", "resolved")
PRIORITIES = ("P1", "P2", "P3", "P4")
CATEGORIES = ("billing", "technical", "account", "other")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class TicketCounter(TenantOwned, Base):
    """Per-tenant ticket numbers (#1, #2, …); one row per tenant, locked FOR UPDATE."""

    __tablename__ = "ticket_counters"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_ticket_counters_tenant"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    last_number: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))


class Ticket(TenantOwned, Timestamped, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "number", name="uq_tickets_tenant_number"),
        UniqueConstraint("tenant_id", "id", name="uq_tickets_tenant_id"),
        ForeignKeyConstraint(["tenant_id", "requester_id"], ["users.tenant_id", "users.id"]),
        ForeignKeyConstraint(["tenant_id", "assignee_id"], ["users.tenant_id", "users.id"]),
        CheckConstraint(_in("status", STATUSES), name="ck_tickets_status"),
        CheckConstraint(_in("priority", PRIORITIES), name="ck_tickets_priority"),
        CheckConstraint(f"category IS NULL OR {_in('category', CATEGORIES)}", name="ck_tickets_category"),
        CheckConstraint("char_length(subject) BETWEEN 1 AND 200", name="ck_tickets_subject_length"),
        Index("ix_tickets_queue", "tenant_id", "created_at", "id"),
        Index("ix_tickets_requester", "tenant_id", "requester_id"),
        Index("ix_tickets_assignee", "tenant_id", "assignee_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    number: Mapped[int] = mapped_column(BigInteger)  # matches ticket_counters.last_number (squawk)
    subject: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=text("'new'"))
    priority: Mapped[str] = mapped_column(Text, server_default=text("'P3'"))
    category: Mapped[str | None] = mapped_column(Text)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    first_replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TicketMessage(TenantOwned, Timestamped, Base):
    __tablename__ = "ticket_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "ticket_id"], ["tickets.tenant_id", "tickets.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(["tenant_id", "author_id"], ["users.tenant_id", "users.id"]),
        CheckConstraint("kind IN ('public','internal')", name="ck_ticket_messages_kind"),
        CheckConstraint("char_length(body) BETWEEN 1 AND 10000", name="ck_ticket_messages_body_length"),
        Index("ix_ticket_messages_ticket", "tenant_id", "ticket_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    # clock_timestamp(), not now(): messages written in one transaction (ticket + first
    # message) still get distinct, ordered timestamps (code review).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
