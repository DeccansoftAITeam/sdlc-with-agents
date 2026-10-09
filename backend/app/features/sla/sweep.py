"""TD-007 breach sweep (design section 4). Run every 30 s by `python -m app.workers.main`.

For each tenant with the flag on, inside that tenant's RLS session, one UPDATE per SLA type
moves breach timestamps from NULL to the database's now(). A row can make that move only
once, so the audit entry and notifications written for RETURNING rows in the same
transaction happen once too (AC-7), however often or concurrently the sweep runs.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from opentelemetry import metrics
from sqlalchemy import ColumnElement, and_, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.db import engine, tenant_session
from app.features.auth.models import Role, User
from app.features.flags.service import SLA_BREACH_ESCALATION, tenants_with
from app.features.notifications.service import notify
from app.features.tickets.models import Ticket

BATCH = 1000  # rows per tenant per SLA type per sweep (TM-016)
LOCK_KEY = "sla_sweep"
log = logging.getLogger("ticketdesk.sla")

_meter = metrics.get_meter("ticketdesk.sla")  # no-op until a MeterProvider is configured (M11)
SWEEP_SECONDS = _meter.create_histogram("sla_sweep_duration_seconds", unit="s")
BREACHES = _meter.create_counter("sla_breaches_detected_total")
LOCK_SKIPPED = _meter.create_counter("sla_sweep_lock_skipped_total")


@dataclass
class SweepResult:
    ran: bool = True
    breaches: list[tuple[uuid.UUID, uuid.UUID, str]] = field(default_factory=list)  # tenant, ticket, type


def _due(sla_type: str) -> tuple[ColumnElement[bool], str]:
    if sla_type == "first_response":
        return (
            and_(
                Ticket.first_response_breached_at.is_(None),
                Ticket.first_replied_at.is_(None),
                Ticket.first_response_due_at <= func.now(),
            ),
            "first_response",
        )
    return (
        and_(
            Ticket.resolution_breached_at.is_(None),
            Ticket.status.not_in(("resolved", "pending_customer")),  # AC-10: paused never breaches
            Ticket.resolution_due_at <= func.now(),
        ),
        "resolution",
    )


async def _sweep_tenant(s: AsyncSession, tenant_id: uuid.UUID) -> list[tuple[uuid.UUID, str]]:
    found: list[tuple[uuid.UUID, str]] = []
    admins = list(
        (await s.execute(select(User.id).where(User.role == Role.ADMIN, User.is_active.is_(True)))).scalars()
    )
    for sla_type in ("first_response", "resolution"):
        condition, name = _due(sla_type)
        column = getattr(Ticket, f"{name}_breached_at")
        deadline = getattr(Ticket, f"{name}_due_at")
        batch = select(Ticket.id).where(condition).limit(BATCH).with_for_update(skip_locked=True)
        rows = await s.execute(
            update(Ticket)
            .where(Ticket.id.in_(batch.scalar_subquery()), condition)
            .values({column: func.now()})
            .returning(Ticket.id, Ticket.number, Ticket.subject, Ticket.assignee_id, deadline, column)
        )
        for ticket_id, number, subject, assignee_id, due_at, detected_at in rows.all():
            await _escalate(
                s, tenant_id, ticket_id, number, subject, assignee_id, name, due_at, detected_at, admins
            )
            found.append((ticket_id, name))
    return found


async def _escalate(
    s: AsyncSession,
    tenant_id: uuid.UUID,
    ticket_id: uuid.UUID,
    number: int,
    subject: str,
    assignee_id: uuid.UUID | None,
    sla_type: str,
    due_at: datetime,
    detected_at: datetime,
    admins: list[uuid.UUID],
) -> None:
    await audit.record(  # AC-6
        s,
        tenant_id=tenant_id,
        actor_id=None,
        action="ticket.sla_breached",
        entity="ticket",
        entity_id=ticket_id,
        data={"sla_type": sla_type, "deadline": due_at.isoformat(), "detected_at": detected_at.isoformat()},
    )
    recipients = [u for u in (assignee_id, *admins) if u is not None]  # AC-4, AC-5; notify() dedupes
    await notify(
        s,
        tenant_id,
        recipients,
        "sla_breached",
        ticket_id,
        {"number": number, "subject": subject, "sla_type": sla_type},
        f"breach:{ticket_id}:{sla_type}",  # AC-7: one per user per (ticket, SLA type), ever
    )


async def sweep() -> SweepResult:
    """One pass over every flagged tenant. Returns what it found (for tests and logs)."""
    started = time.monotonic()
    async with engine().connect() as lock_conn:
        got = (
            await lock_conn.execute(text("SELECT pg_try_advisory_lock(hashtext(:k))"), {"k": LOCK_KEY})
        ).scalar_one()
        await lock_conn.commit()  # session lock survives; don't sit idle in a transaction
        if not got:  # another worker is sweeping; the next tick will catch up
            LOCK_SKIPPED.add(1)
            return SweepResult(ran=False)
        result = SweepResult()
        try:
            for tenant_id in await tenants_with(SLA_BREACH_ESCALATION):  # AC-14: flag off = skipped
                try:
                    async with tenant_session(tenant_id) as s:  # AC-8: RLS scopes every statement
                        found = await _sweep_tenant(s, tenant_id)
                except Exception:  # one bad tenant must not stall the others (security review)
                    log.exception("sla sweep failed for tenant %s", tenant_id)
                    continue
                for ticket_id, sla_type in found:
                    result.breaches.append((tenant_id, ticket_id, sla_type))
                    BREACHES.add(1, {"sla_type": sla_type})
            return result
        finally:
            try:
                await lock_conn.execute(text("SELECT pg_advisory_unlock(hashtext(:k))"), {"k": LOCK_KEY})
                await lock_conn.commit()
            except Exception:
                # Never return a connection that may still hold the lock to the pool.
                await lock_conn.invalidate()
                raise
            finally:
                SWEEP_SECONDS.record(time.monotonic() - started)
