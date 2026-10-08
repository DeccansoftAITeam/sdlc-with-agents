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
    """Tenants are created only through the SECURITY DEFINER function (no table access)."""
    async with system_session() as s:
        tid = (
            await s.execute(text("SELECT create_tenant(:slug, :name)"), {"slug": slug, "name": slug.title()})
        ).scalar_one()
    assert isinstance(tid, uuid.UUID)
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
    """Expand-only migration must downgrade cleanly and re-apply (migration-writer step 7).

    Runs against the shared test DB, so the suite must stay serial (no pytest-xdist -n).
    """
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


_ROW_SQL = {
    "users": "INSERT INTO users (tenant_id, email, name, password_hash, role) "
    "VALUES (:t, :e, 'N', 'x', 'customer')",
    "refresh_tokens": "INSERT INTO refresh_tokens (tenant_id, user_id, family_id, token_hash, expires_at) "
    "VALUES (:t, :u, gen_random_uuid(), :h, now() + interval '7 days')",
    "email_tokens": "INSERT INTO email_tokens (tenant_id, user_id, purpose, token_hash, expires_at) "
    "VALUES (:t, :u, 'verify', :h, now() + interval '30 minutes')",
}


@pytest.mark.parametrize("table", list(_ROW_SQL))
async def test_rows_invisible_across_tenants(table: str) -> None:
    """Every tenant table (not just users) hides rows from other tenants (TM-003)."""
    a, b = await _tenant(_slug()), await _tenant(_slug())
    uid = await _user(a, f"{uuid.uuid4().hex[:8]}@example.com")
    async with tenant_session(a) as s:
        await s.execute(
            text(_ROW_SQL[table]), {"t": a, "u": uid, "e": "row@example.com", "h": uuid.uuid4().hex * 2}
        )
    async with tenant_session(b) as s:
        n = (
            await s.execute(text(f"SELECT count(*) FROM {table} WHERE tenant_id = :t"), {"t": a})
        ).scalar_one()
    assert n == 0


@pytest.mark.parametrize("table", list(_ROW_SQL))
async def test_cannot_insert_into_another_tenant(table: str) -> None:
    a, b = await _tenant(_slug()), await _tenant(_slug())
    uid = await _user(a, f"{uuid.uuid4().hex[:8]}@example.com")
    with pytest.raises(DBAPIError, match="row-level security"):
        async with tenant_session(b) as s:
            await s.execute(
                text(_ROW_SQL[table]), {"t": a, "u": uid, "e": "x@example.com", "h": uuid.uuid4().hex * 2}
            )


async def test_token_hash_must_be_sha256_hex_length() -> None:
    a = await _tenant(_slug())
    uid = await _user(a, "len@example.com")
    with pytest.raises(IntegrityError, match="ck_email_tokens_hash_len"):
        async with tenant_session(a) as s:
            await s.execute(
                text(
                    "INSERT INTO email_tokens (tenant_id, user_id, purpose, token_hash, expires_at) "
                    "VALUES (:t, :u, 'verify', 'short', now() + interval '30 minutes')"
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


# --- security-reviewer findings (T-001-01 review) -------------------------------------


async def test_app_role_has_no_direct_access_to_tenants_registry() -> None:
    """Finding 1: runtime role can't list, rename or delete tenants (ADR-0003, TM-003)."""
    await _tenant(_slug())
    for sql in ("SELECT * FROM tenants", "UPDATE tenants SET name = 'x'", "DELETE FROM tenants"):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with system_session() as s:
                await s.execute(text(sql))


async def test_resolve_tenant_slug() -> None:
    slug = _slug()
    tid = await _tenant(slug)
    async with system_session() as s:
        assert (await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one() == tid
        assert (await s.execute(text("SELECT resolve_tenant_slug('nope-nope')"))).scalar_one() is None


async def test_tenant_slug_is_immutable(owner_engine: AsyncEngine) -> None:
    slug = _slug()
    await _tenant(slug)
    with pytest.raises(DBAPIError, match="immutable"):
        async with owner_engine.begin() as c:
            await c.execute(text("UPDATE tenants SET slug = 'renamed-x' WHERE slug = :s"), {"s": slug})


async def test_user_requires_existing_tenant() -> None:
    """Finding 2: no orphan users under a tenant id that doesn't exist."""
    ghost = uuid.uuid4()
    with pytest.raises(IntegrityError, match="fk_users_tenant"):
        await _user(ghost, "ghost@example.com")


async def test_only_one_live_email_token_per_user_and_purpose() -> None:
    """Finding 3 (TM-014): a second live reset link is rejected until the first is consumed."""
    a = await _tenant(_slug())
    uid = await _user(a, "reset@example.com")
    ins = text(
        "INSERT INTO email_tokens (tenant_id, user_id, purpose, token_hash, expires_at) "
        "VALUES (:t, :u, 'reset', :h, now() + interval '30 minutes')"
    )
    async with tenant_session(a) as s:
        await s.execute(ins, {"t": a, "u": uid, "h": "1" * 64})
    with pytest.raises(IntegrityError, match="uq_email_tokens_one_live"):
        async with tenant_session(a) as s:
            await s.execute(ins, {"t": a, "u": uid, "h": "2" * 64})
    async with tenant_session(a) as s:  # consume the first, then a new one is allowed
        await s.execute(
            text("UPDATE email_tokens SET used_at = now() WHERE token_hash = :h"), {"h": "1" * 64}
        )
        await s.execute(ins, {"t": a, "u": uid, "h": "2" * 64})


async def test_token_cannot_expire_before_creation() -> None:
    """Finding 4 (TM-001): expiry must be after creation."""
    a = await _tenant(_slug())
    uid = await _user(a, "exp@example.com")
    with pytest.raises(IntegrityError, match="ck_refresh_tokens_expiry"):
        async with tenant_session(a) as s:
            await s.execute(
                text(
                    "INSERT INTO refresh_tokens (tenant_id, user_id, family_id, token_hash, expires_at) "
                    "VALUES (:t, :u, gen_random_uuid(), :h, now() - interval '1 minute')"
                ),
                {"t": a, "u": uid, "h": "3" * 64},
            )
