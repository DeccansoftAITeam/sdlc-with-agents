"""In-app notifications (TD-006). Tenant-owned with forced RLS (migration td006a)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TenantOwned


class Notification(TenantOwned, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "dedupe_key", name="uq_notifications_dedupe"),
        ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["tenant_id", "ticket_id"], ["tickets.tenant_id", "tickets.id"], ondelete="CASCADE"
        ),
        Index("ix_notifications_inbox", "tenant_id", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(Text)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    dedupe_key: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # clock_timestamp(): several notifications in one transaction still sort newest-first.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
