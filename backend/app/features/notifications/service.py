"""TD-006 notifications. `notify` writes inside the CALLER's transaction, so a notification
exists only if the change that caused it commits. Payloads carry the ticket number and
subject only, never message bodies (TD-006 design notes).
"""

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import tenant_session
from app.core.errors import ProblemError
from app.core.security import Principal
from app.features.notifications.models import Notification

INBOX_SIZE = 50
RETENTION = timedelta(days=90)


async def notify(
    s: AsyncSession,
    tenant_id: uuid.UUID,
    user_ids: Iterable[uuid.UUID],
    kind: str,
    ticket_id: uuid.UUID | None,
    payload: dict[str, Any],
    dedupe_key: str,
) -> None:
    """One row per user; a repeat of the same dedupe_key for a user is ignored (AC-1)."""
    rows = [
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "kind": kind,
            "ticket_id": ticket_id,
            "payload": payload,
            "dedupe_key": dedupe_key,
        }
        for user_id in dict.fromkeys(user_ids)
    ]
    if rows:
        await s.execute(
            insert(Notification).values(rows).on_conflict_do_nothing(constraint="uq_notifications_dedupe")
        )


async def inbox(who: Principal) -> tuple[list[Notification], int]:
    mine = Notification.user_id == who.user_id  # AC-6: RLS scopes the tenant, this scopes the user
    async with tenant_session(who.tenant_id) as s:
        items = await s.execute(
            select(Notification).where(mine).order_by(Notification.created_at.desc()).limit(INBOX_SIZE)
        )
        unread = await s.execute(
            select(func.count()).select_from(Notification).where(mine, Notification.read_at.is_(None))
        )
        return list(items.scalars()), int(unread.scalar_one())


async def mark_read(who: Principal, notification_id: uuid.UUID | None) -> None:
    """Mark one (or, with None, all) of the caller's notifications read (AC-3)."""
    mine = Notification.user_id == who.user_id
    async with tenant_session(who.tenant_id) as s:
        q = update(Notification).where(mine, Notification.read_at.is_(None))
        if notification_id is not None:
            found = await s.execute(select(Notification.id).where(mine, Notification.id == notification_id))
            if found.scalar_one_or_none() is None:
                raise ProblemError(404, "Not Found")  # someone else's looks the same as none
            q = q.where(Notification.id == notification_id)
        await s.execute(q.values(read_at=func.now()))


async def purge_expired(tenant_id: uuid.UUID, now: datetime | None = None) -> int:
    """Delete one tenant's notifications older than 90 days (AC-7). The scheduled loop over
    all tenants arrives with the TD-007 job runner."""
    cutoff = (now or datetime.now(UTC)) - RETENTION
    async with tenant_session(tenant_id) as s:
        result = await s.execute(delete(Notification).where(Notification.created_at < cutoff))
        return int(result.rowcount)  # type: ignore[attr-defined]
