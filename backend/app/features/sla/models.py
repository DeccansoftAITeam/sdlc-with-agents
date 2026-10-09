"""Per-tenant SLA policy (TD-005). Tenant-owned with forced RLS (migration td005a)."""

import uuid
from typing import Any

from sqlalchemy import Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TenantOwned


class TenantSlaSettings(TenantOwned, Base):
    __tablename__ = "tenant_sla_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tenant_sla_settings_tenant"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    targets: Mapped[dict[str, Any]] = mapped_column(JSONB)
    timezone: Mapped[str] = mapped_column(Text)
    schedule: Mapped[dict[str, Any]] = mapped_column(JSONB)
