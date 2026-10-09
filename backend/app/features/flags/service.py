"""Per-tenant feature flags. Every flag defaults to OFF; only keys in KNOWN_FLAGS exist."""

import uuid

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.db import system_session, tenant_session
from app.core.errors import ProblemError
from app.core.security import Principal
from app.features.flags.models import FeatureFlag

SLA_BREACH_ESCALATION = "sla-breach-escalation"  # TD-007, remove by 2026-12-31
KNOWN_FLAGS = (SLA_BREACH_ESCALATION,)


async def is_enabled(s: AsyncSession, key: str) -> bool:
    """For the tenant of the caller's RLS session."""
    found = await s.execute(select(FeatureFlag.enabled).where(FeatureFlag.key == key))
    return bool(found.scalar_one_or_none())


async def tenants_with(key: str) -> list[uuid.UUID]:
    """Tenant ids with the flag on, via the narrow SECURITY DEFINER function (td007a)."""
    async with system_session() as s:
        rows = await s.execute(text("SELECT tenants_with_flag(:k)"), {"k": key})
        return [uuid.UUID(str(r[0])) for r in rows]


async def get_all(who: Principal) -> dict[str, bool]:
    async with tenant_session(who.tenant_id) as s:
        return {key: await is_enabled(s, key) for key in KNOWN_FLAGS}


async def set_flag(who: Principal, key: str, enabled: bool) -> None:
    if key not in KNOWN_FLAGS:
        raise ProblemError(404, "Not Found", "Unknown flag.")
    async with tenant_session(who.tenant_id) as s:
        old = await is_enabled(s, key)
        stmt = insert(FeatureFlag).values(tenant_id=who.tenant_id, key=key, enabled=enabled)
        await s.execute(
            stmt.on_conflict_do_update(constraint="uq_feature_flags_tenant_key", set_={"enabled": enabled})
        )
        if old != enabled:
            await audit.record(
                s,
                tenant_id=who.tenant_id,
                actor_id=who.user_id,
                action="flag.changed",
                entity="tenant",
                entity_id=who.tenant_id,
                data={"flag": key, "from": old, "to": enabled},
            )
