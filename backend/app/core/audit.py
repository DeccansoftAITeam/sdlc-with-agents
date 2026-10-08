"""Append-only audit log (TM-008 repudiation; TD-002/AC-7, reused by TD-004 and TD-007).

The runtime database role may INSERT and SELECT audit rows but has no UPDATE or DELETE
privilege (migration td002a), so history can't be rewritten through the app. Never put
personal data or message content in `data`: ids and field values only.
"""

import uuid
from typing import Any

from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from app.core.models import Base, TenantOwned, Timestamped


class AuditEntry(TenantOwned, Timestamped, Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_entity", "tenant_id", "entity_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(Text)  # e.g. "user.role_changed"
    entity: Mapped[str] = mapped_column(Text)  # e.g. "user", "ticket"
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))


async def record(
    s: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    action: str,
    entity: str,
    entity_id: uuid.UUID,
    data: dict[str, Any] | None = None,
) -> None:
    """Add an audit row in the caller's transaction (so it commits or rolls back with the change)."""
    s.add(
        AuditEntry(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            data=data or {},
        )
    )
