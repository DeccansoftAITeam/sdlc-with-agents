"""Declarative base and the tenant-owned mixin.

Any model using `TenantOwned` gets a `tenant_id` column. Its migration MUST
enable and force row-level security with the `tenant_isolation` policy
(`migrations/rls.py: enable_rls`). tests/architecture/test_rls_coverage.py fails
the build if a table with a tenant_id column lacks forced RLS.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TenantOwned:
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
