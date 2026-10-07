"""Database engine and the tenant-scoped session helper.

Every request and every background job that touches tenant data MUST use
`tenant_session(tenant_id)`. It opens a transaction and sets the Postgres
setting `app.tenant_id` with SET LOCAL semantics, which row-level-security
policies read. Without it, RLS policies match nothing: the system fails closed.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def sessionmaker() -> async_sessionmaker[AsyncSession]:
    engine()
    assert _sessionmaker is not None
    return _sessionmaker


@asynccontextmanager
async def tenant_session(tenant_id: UUID) -> AsyncIterator[AsyncSession]:
    """Transaction scoped to one tenant. Commits on success, rolls back on error."""
    async with sessionmaker()() as session, session.begin():
        # set_config(..., is_local => true) == SET LOCAL: reset at transaction end,
        # so a pooled connection never carries one tenant's id into another request.
        await session.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)})
        yield session


@asynccontextmanager
async def system_session() -> AsyncIterator[AsyncSession]:
    """Transaction WITHOUT a tenant. RLS-protected tables return no rows here.

    Use only for tables that are not tenant-owned (e.g. the tenants registry)
    through narrow, tested functions.
    """
    async with sessionmaker()() as session, session.begin():
        yield session
