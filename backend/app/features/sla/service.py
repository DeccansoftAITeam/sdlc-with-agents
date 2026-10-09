"""TD-005 policy storage and the bridge from stored JSON to the pure deadline function.

A tenant without a row uses DEFAULT_POLICY (AC-1): every tenant has the constitution §8
defaults from the moment it exists, with no extra write in signup. Tickets snapshot the
policy at creation (AC-2), so editing the policy never moves an existing ticket's deadline.
"""

from datetime import datetime, time
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.db import tenant_session
from app.core.security import Principal
from app.features.sla.deadlines import Deadlines, Schedule, Target, compute_deadlines
from app.features.sla.models import TenantSlaSettings
from app.features.sla.schemas import SlaSettingsIO

BUSINESS_DAY = 9 * 60  # minutes in the default 09:00-18:00 day
DEFAULT_POLICY: dict[str, Any] = {
    "targets": {
        "P1": {"first_response_minutes": 60, "resolution_minutes": 8 * 60},
        "P2": {"first_response_minutes": 4 * 60, "resolution_minutes": BUSINESS_DAY},
        "P3": {"first_response_minutes": BUSINESS_DAY, "resolution_minutes": 3 * BUSINESS_DAY},
        "P4": {"first_response_minutes": 3 * BUSINESS_DAY, "resolution_minutes": 10 * BUSINESS_DAY},
    },
    "timezone": "UTC",
    "schedule": {"days": [0, 1, 2, 3, 4], "start": "09:00:00", "end": "18:00:00"},
}


async def policy(s: AsyncSession) -> dict[str, Any]:
    """The current tenant's policy as plain JSON (the caller's RLS session picks the tenant)."""
    row = (await s.execute(select(TenantSlaSettings))).scalar_one_or_none()
    if row is None:
        return DEFAULT_POLICY
    return {"targets": row.targets, "timezone": row.timezone, "schedule": row.schedule}


async def get_settings(who: Principal) -> dict[str, Any]:
    async with tenant_session(who.tenant_id) as s:
        return await policy(s)


async def put_settings(who: Principal, data: SlaSettingsIO) -> dict[str, Any]:
    new = data.model_dump(mode="json")
    async with tenant_session(who.tenant_id) as s:
        old = await policy(s)
        stmt = insert(TenantSlaSettings).values(tenant_id=who.tenant_id, **new)
        await s.execute(
            stmt.on_conflict_do_update(
                constraint="uq_tenant_sla_settings_tenant",
                set_={k: stmt.excluded[k] for k in ("targets", "timezone", "schedule")},
            )
        )
        await audit.record(
            s,
            tenant_id=who.tenant_id,
            actor_id=who.user_id,
            action="sla_settings.changed",
            entity="tenant",
            entity_id=who.tenant_id,
            data={"from": old, "to": new},
        )
    return new


def deadlines(
    snapshot: dict[str, Any], created_at: datetime, priority: str, pauses: list[list[str | None]]
) -> Deadlines:
    sched = snapshot["schedule"]
    return compute_deadlines(
        created_at,
        priority,
        [(datetime.fromisoformat(str(a)), datetime.fromisoformat(b) if b else None) for a, b in pauses],
        {p: Target(**t) for p, t in snapshot["targets"].items()},
        Schedule(
            frozenset(sched["days"]), time.fromisoformat(sched["start"]), time.fromisoformat(sched["end"])
        ),
        snapshot["timezone"],
    )
