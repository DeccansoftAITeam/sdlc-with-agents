"""T-001-01: TD-001 tables enforce per-tenant identity and isolation in the database itself."""

import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.db import system_session, tenant_session

BACKEND = Path(__file__).resolve().parents[2]
HASH = "a" * 64


async def _tenant(slug: str) -> uuid.UUID:
    tid = uuid.uuid4()
    async with system_session() as s:
        await s.execute(
            text("INSERT INTO tenants (id, slug, name) VALUES (:id, :slug, :name)"),
            {"id": tid, "slug": slug, "name": slug.title()},
        )
    return tid


async def _user(tid: uuid.UUID, email: str, role: str = "customer") -> uuid.UUID:
    uid = uuid.uuid4()
    async with tenant_session(tid) as s:
        await s.execute(
            text(
                "INSERT INTO users (id, tenant_id, email, name, password_hash, role) "
                "VALUES (:id, :t, :e, 'N', 'x', :r)"
            ),
            {"id": uid, "t": tid, "e": email, "r": role},
        )
    return uid


def _slug() -> str:
    return f"t-{uuid.uuid4().hex[:8]}"


def test_migration_round_trip() -> None:
    """Expand-only migration must downgrade cleanly and re-apply (migration-writer step 7)."""
    for args in (["downgrade", "0001"], ["upgrade", "head"]):
        subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, check=True)


async def test_same_email_allowed_in_two_tenants() -> None:
    """Identity is per tenant (constitution principle 5, grill Q2)."""
    a, b = await _tenant(_slug()), await _tenant(_slug())
    await _user(a, "pat@example.com")
    await _user(b, "pat@example.com")


async def test_duplicate_email_rejected_within_a_tenant() -> None:
    a = await _tenant(_slug())
    await _user(a, "sam@example.com")
    with pytest.raises(IntegrityError, match="uq_users_tenant_email"):
        await _user(a, "sam@example.com")


async def test_email_must_be_lowercase() -> None:
    a = await _tenant(_slug())
    with pytest.raises(IntegrityError, match="ck_users_email_lowercase"):
        await _user(a, "Sam@Example.com")


@pytest.mark.parametrize("slug", ["ab", "Has-Caps", "under_score", "x" * 41])
async def test_invalid_slug_rejected(slug: str) -> None:
    with pytest.raises(IntegrityError, match="ck_tenants_slug_format"):
        await _tenant(slug)


async def test_token_cannot_reference_another_tenants_user() -> None:
    """Composite FK (tenant_id, user_id): defence in depth beyond RLS (TM-003)."""
    a, b = await _tenant(_slug()), await _tenant(_slug())
    user_in_a = await _user(a, "victim@example.com")
    with pytest.raises(IntegrityError, match="foreign key"):
        async with tenant_session(b) as s:
            await s.execute(
                text(
                    "INSERT INTO refresh_tokens (tenant_id, user_id, family_id, token_hash, expires_at) "
                    "VALUES (:t, :u, :f, :h, :x)"
                ),
                {
                    "t": b,
                    "u": user_in_a,
                    "f": uuid.uuid4(),
                    "h": HASH,
                    "x": datetime.now(UTC) + timedelta(days=7),
                },
            )


async def test_users_invisible_across_tenants() -> None:
    a, b = await _tenant(_slug()), await _tenant(_slug())
    await _user(a, "only-in-a@example.com")
    async with tenant_session(b) as s:
        n = (
            await s.execute(text("SELECT count(*) FROM users WHERE email = 'only-in-a@example.com'"))
        ).scalar_one()
    assert n == 0


async def test_cannot_insert_user_into_another_tenant() -> None:
    a, b = await _tenant(_slug()), await _tenant(_slug())
    with pytest.raises(DBAPIError, match="row-level security"):
        async with tenant_session(b) as s:
            await s.execute(
                text(
                    "INSERT INTO users (tenant_id, email, name, password_hash, role) "
                    "VALUES (:t, 'x@example.com', 'N', 'x', 'admin')"
                ),
                {"t": a},
            )


async def test_token_hash_must_be_sha256_hex_length() -> None:
    a = await _tenant(_slug())
    uid = await _user(a, "len@example.com")
    with pytest.raises(IntegrityError, match="ck_email_tokens_hash_len"):
        async with tenant_session(a) as s:
            await s.execute(
                text(
                    "INSERT INTO email_tokens (tenant_id, user_id, purpose, token_hash, expires_at) "
                    "VALUES (:t, :u, 'verify', 'short', now())"
                ),
                {"t": a, "u": uid},
            )


async def test_models_match_migrations(owner_engine: AsyncEngine) -> None:
    """ORM models and migrations must agree: catches 'changed a model, forgot the migration'."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    from app.core.models import Base
    from app.features import load_models

    load_models()

    def diff(conn: Connection) -> list[object]:
        ctx = MigrationContext.configure(conn, opts={"compare_type": True, "compare_server_default": True})
        return list(compare_metadata(ctx, Base.metadata))

    async with owner_engine.connect() as c:
        changes = await c.run_sync(diff)
    assert changes == [], f"models and migrations differ: {changes}"
