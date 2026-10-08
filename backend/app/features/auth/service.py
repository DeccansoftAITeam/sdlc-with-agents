"""TD-001 self-serve signup (T-001-02, as amended 2026-10-08: no email).

Signup creates the tenant and its first admin in ONE transaction; the admin can log in
immediately (no email verification). Invite and reset links are admin-issued (T-002-01).
"""

import uuid

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.db import sessionmaker
from app.core.errors import ProblemError
from app.features.auth.models import Role, User
from app.features.auth.passwords import enforce_policy, hash_password
from app.features.auth.schemas import SignupIn

RESERVED_SLUGS = frozenset({"api", "admin", "t", "login", "signup", "static", "health"})
SLUG_UNIQUE = "tenants_slug_key"  # Postgres default name for tenants.slug UNIQUE (migration td001a)


def _constraint(exc: IntegrityError) -> str | None:
    """Constraint name from the driver error (asyncpg), not from parsing the message."""
    cause = getattr(exc.orig, "__cause__", None)
    name = getattr(cause, "constraint_name", None)
    return name if isinstance(name, str) else None


async def signup(data: SignupIn) -> str:
    if data.slug in RESERVED_SLUGS:
        raise ProblemError(422, "Slug not available", "This address is reserved.")
    enforce_policy(data.password)
    password_hash = hash_password(data.password)
    try:
        async with sessionmaker()() as s, s.begin():
            tid = uuid.UUID(
                str(
                    (
                        await s.execute(
                            text("SELECT create_tenant(:slug, :name)"),
                            {"slug": data.slug, "name": data.company_name},
                        )
                    ).scalar_one()
                )
            )
            # Same transaction, now scoped to the new tenant so RLS applies to the insert.
            await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})
            s.add(
                User(
                    tenant_id=tid,
                    email=data.email,
                    name=data.admin_name,
                    password_hash=password_hash,
                    role=Role.ADMIN,
                )
            )
    except IntegrityError as exc:
        if _constraint(exc) == SLUG_UNIQUE:
            raise ProblemError(409, "Slug not available", "Choose another address.") from None
        raise
    return data.slug
