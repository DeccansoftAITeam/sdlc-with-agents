"""Proves the tenant-isolation mechanism (ADR: multi-tenancy, threat TM-003).

Uses a throwaway table created by the owner with the same policy every tenant
table gets, then queries it as the runtime app role through `tenant_session`.
"""

import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.db import system_session, tenant_session

A, B = uuid.uuid4(), uuid.uuid4()


@pytest.fixture(scope="module")
async def probe(owner_engine: AsyncEngine) -> AsyncIterator[None]:
    async with owner_engine.begin() as c:
        await c.execute(text("DROP TABLE IF EXISTS rls_probe"))
        await c.execute(
            text("CREATE TABLE rls_probe (id serial PRIMARY KEY, tenant_id uuid NOT NULL, v text)")
        )
        await c.execute(text("ALTER TABLE rls_probe ENABLE ROW LEVEL SECURITY"))
        await c.execute(text("ALTER TABLE rls_probe FORCE ROW LEVEL SECURITY"))
        await c.execute(
            text(
                "CREATE POLICY tenant_isolation ON rls_probe USING (tenant_id = app_current_tenant()) "
                "WITH CHECK (tenant_id = app_current_tenant())"
            )
        )
    for tid, v in ((A, "a-secret"), (B, "b-secret")):
        async with tenant_session(tid) as s:
            await s.execute(text("INSERT INTO rls_probe (tenant_id, v) VALUES (:t, :v)"), {"t": tid, "v": v})
    yield
    async with owner_engine.begin() as c:
        await c.execute(text("DROP TABLE rls_probe"))


async def test_tenant_sees_only_own_rows(probe: None) -> None:
    async with tenant_session(A) as s:
        rows = (await s.execute(text("SELECT v FROM rls_probe"))).scalars().all()
    assert rows == ["a-secret"]


async def test_no_tenant_set_sees_nothing(probe: None) -> None:
    async with system_session() as s:
        assert (await s.execute(text("SELECT count(*) FROM rls_probe"))).scalar_one() == 0


async def test_cannot_write_other_tenants_row(probe: None) -> None:
    with pytest.raises(DBAPIError, match="row-level security"):
        async with tenant_session(A) as s:
            await s.execute(text("INSERT INTO rls_probe (tenant_id, v) VALUES (:t, 'x')"), {"t": B})


async def test_tenant_setting_does_not_leak_across_transactions(probe: None) -> None:
    async with tenant_session(A):
        pass
    async with system_session() as s:
        val = (await s.execute(text("SELECT current_setting('app.tenant_id', true)"))).scalar_one()
    assert val in (None, "")


async def test_app_role_cannot_disable_rls(app_engine: AsyncEngine, probe: None) -> None:
    async with app_engine.connect() as c:
        await c.execute(text("SET row_security = off"))
        with pytest.raises(DBAPIError, match="row-level security"):
            await c.execute(text("SELECT * FROM rls_probe"))
