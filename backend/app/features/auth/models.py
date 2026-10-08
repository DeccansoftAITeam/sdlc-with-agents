"""TD-001 data model (ADR-0002 auth, ADR-0003 multi-tenancy).

- `tenants` is the registry, not tenant-owned (no RLS). Access it only through narrow
  functions; it holds no personal data.
- Every other table is tenant-owned with forced RLS. Child rows reference users via
  the composite key (tenant_id, user_id), so a row can never point at another
  tenant's user even if application code is wrong.
- Tokens are stored as SHA-256 hashes only, never in clear text (TM-001, TM-014).
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
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


class Role(StrEnum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class EmailTokenPurpose(StrEnum):
    VERIFY = "verify"
    RESET = "reset"


class Tenant(Timestamped, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(r"slug ~ '^[a-z0-9-]{3,40}$'", name="ck_tenants_slug_format"),
        CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="ck_tenants_name_length"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    slug: Mapped[str] = mapped_column(Text, unique=True)  # immutable after creation
    name: Mapped[str] = mapped_column(Text)


class User(TenantOwned, Timestamped, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        UniqueConstraint("tenant_id", "id", name="uq_users_tenant_id"),  # target of composite FKs
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
        CheckConstraint("char_length(email) BETWEEN 3 AND 320", name="ck_users_email_length"),
        CheckConstraint("char_length(name) BETWEEN 1 AND 200", name="ck_users_name_length"),
        CheckConstraint("role IN ('admin','staff','customer')", name="ck_users_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)  # Argon2id encoded hash
    role: Mapped[str] = mapped_column(Text)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class RefreshToken(TenantOwned, Timestamped, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"], ondelete="CASCADE"),
        Index("ix_refresh_tokens_family", "tenant_id", "family_id"),
        Index("ix_refresh_tokens_user", "tenant_id", "user_id"),  # backs the composite FK
        CheckConstraint("char_length(token_hash) = 64", name="ck_refresh_tokens_hash_len"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))  # reuse revokes the family
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EmailToken(TenantOwned, Timestamped, Base):
    __tablename__ = "email_tokens"
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"], ondelete="CASCADE"),
        Index("ix_email_tokens_user", "tenant_id", "user_id"),  # backs the composite FK
        CheckConstraint("purpose IN ('verify','reset')", name="ck_email_tokens_purpose"),
        CheckConstraint("char_length(token_hash) = 64", name="ck_email_tokens_hash_len"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    purpose: Mapped[str] = mapped_column(Text)
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


__all__ = ["EmailToken", "EmailTokenPurpose", "RefreshToken", "Role", "Tenant", "User"]
