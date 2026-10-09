"""TD-003 / TD-004 services. Every query runs in the caller's tenant RLS session.

Visibility rules: staff and admins see every ticket of their tenant; customers see only
tickets they requested, and never internal notes. A ticket a caller may not see is a
404, never a 403, so its existence isn't revealed (TD-003/AC-6).
"""

import base64
import binascii
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ColumnElement, and_, case, func, literal, or_, select, text, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.db import tenant_session
from app.core.errors import ProblemError
from app.core.security import Principal
from app.features.auth.models import Role, User
from app.features.flags import service as flags
from app.features.notifications.service import notify
from app.features.sla import service as sla
from app.features.tickets import workflow
from app.features.tickets.models import Ticket, TicketMessage
from app.features.tickets.schemas import MessageIn, TicketCreateIn, TicketPatchIn

STAFF_ROLES = (Role.ADMIN, Role.STAFF)
NOT_FOUND = ProblemError(404, "Not Found")
STAFF_ONLY = ProblemError(403, "Forbidden", "Only staff can do this.")


def is_staff(p: Principal) -> bool:
    return p.role in STAFF_ROLES


async def _next_number(s: AsyncSession, tenant_id: uuid.UUID) -> int:
    row = await s.execute(
        text(
            "INSERT INTO ticket_counters (tenant_id, last_number) VALUES (:t, 1) "
            "ON CONFLICT (tenant_id) DO UPDATE SET last_number = ticket_counters.last_number + 1 "
            "RETURNING last_number"
        ),
        {"t": tenant_id},
    )
    return int(row.scalar_one())


async def _user_with_role(s: AsyncSession, user_id: uuid.UUID, roles: tuple[str, ...]) -> bool:
    found = await s.execute(
        select(User.id).where(User.id == user_id, User.role.in_(roles), User.is_active.is_(True))
    )
    return found.scalar_one_or_none() is not None


async def _audit_change(
    s: AsyncSession, who: Principal, ticket: Ticket, field: str, old: Any, new: Any
) -> None:
    def plain(v: Any) -> Any:
        return str(v) if isinstance(v, uuid.UUID) else v

    await audit.record(
        s,
        tenant_id=who.tenant_id,
        actor_id=who.user_id,
        action=f"ticket.{field}_changed",
        entity="ticket",
        entity_id=ticket.id,
        data={"from": plain(old), "to": plain(new)},
    )


def _recompute_deadlines(ticket: Ticket) -> None:
    """TD-004/AC-7, TD-005/AC-7: the only place stored deadlines change."""
    if ticket.sla_policy is None:  # created before td005a: no SLA to track
        return
    due = sla.deadlines(ticket.sla_policy, ticket.created_at, ticket.priority, ticket.paused_intervals)
    ticket.first_response_due_at = due.first_response_due_at
    ticket.resolution_due_at = due.resolution_due_at


# Statuses that stop the resolution clock: waiting on the customer (TD-005/AC-5) and
# resolved, so a reopened ticket resumes from the time already consumed (TD-007/AC-11).
PAUSING = ("pending_customer", "resolved")


def _track_pause(ticket: Ticket, old: str, new: str, now: str) -> None:
    """Open a pause on entering a pausing status, close it on leaving them all."""
    pauses = [list(p) for p in ticket.paused_intervals]  # new list: JSONB changes must be reassigned
    if new in PAUSING and old not in PAUSING:
        pauses.append([now, None])
    elif old in PAUSING and new not in PAUSING:
        if pauses and pauses[-1][1] is None:
            pauses[-1][1] = now
        elif old == "resolved" and ticket.resolved_at is not None:
            # Resolved before td007 recorded resolve-pauses: the pause began at resolved_at
            # (code review: else reopening an old ticket breaches it at once).
            pauses.append([ticket.resolved_at.isoformat(), now])
    ticket.paused_intervals = pauses


async def _set_status(s: AsyncSession, who: Principal, ticket: Ticket, new: str) -> None:
    if new == ticket.status:
        return
    await _audit_change(s, who, ticket, "status", ticket.status, new)
    # Database clock, like created_at, so pauses and creation never disagree (code review).
    now = (await s.execute(text("SELECT clock_timestamp()"))).scalar_one().isoformat()
    _track_pause(ticket, ticket.status, new, now)
    ticket.status = new
    ticket.resolved_at = func.now() if new == "resolved" else None
    _recompute_deadlines(ticket)


async def create(who: Principal, data: TicketCreateIn) -> Ticket:
    async with tenant_session(who.tenant_id) as s:
        if is_staff(who):
            if data.requester_id is None or not await _user_with_role(s, data.requester_id, (Role.CUSTOMER,)):
                raise ProblemError(422, "Invalid requester", "Name an active customer of this tenant.")
            requester, priority, category = data.requester_id, data.priority or "P3", data.category
        else:
            if data.priority is not None or data.category is not None or data.requester_id is not None:
                raise ProblemError(422, "Not allowed", "Customers can't set priority, category or requester.")
            requester, priority, category = who.user_id, "P3", None
        ticket = Ticket(
            tenant_id=who.tenant_id,
            number=await _next_number(s, who.tenant_id),
            subject=data.subject,
            priority=priority,
            category=category,
            requester_id=requester,
            sla_policy=await sla.policy(s),  # snapshot: later policy edits don't move it (TD-005/AC-2)
            paused_intervals=[],
        )
        s.add(ticket)
        await s.flush()
        await s.refresh(ticket)  # created_at comes from the database clock
        _recompute_deadlines(ticket)
        s.add(
            TicketMessage(
                tenant_id=who.tenant_id,
                ticket_id=ticket.id,
                author_id=who.user_id,
                kind="public",
                body=data.body,
            )
        )
        await s.flush()
        await s.refresh(ticket)
        return ticket


FAR_FUTURE = datetime(9999, 1, 1, tzinfo=UTC)  # sorts "not breach-active" last


def breach_active_at() -> ColumnElement[datetime]:
    """TD-007 design section 5: earliest breach that still needs action, else FAR_FUTURE."""
    unresolved = Ticket.status != "resolved"
    return func.coalesce(
        func.least(
            case(
                (and_(Ticket.first_replied_at.is_(None), unresolved), Ticket.first_response_breached_at),
            ),
            case((unresolved, Ticket.resolution_breached_at)),
        ),
        FAR_FUTURE,
    )


def _encode_cursor(t: Ticket, active_at: datetime) -> str:
    raw = f"{active_at.isoformat()}|{t.created_at.isoformat()}|{t.number}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, datetime, int]:
    try:
        active, created, number = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        when, at = datetime.fromisoformat(created), datetime.fromisoformat(active)
        if when.tzinfo is None or at.tzinfo is None:
            raise ValueError("cursor timestamps must be timezone-aware")
        return at, when, int(number)
    except (ValueError, binascii.Error, UnicodeDecodeError):
        raise ProblemError(422, "Invalid cursor") from None


async def queue(
    who: Principal,
    *,
    status: str | None,
    priority: str | None,
    assignee_id: uuid.UUID | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[tuple[Ticket, bool]], str | None]:
    """Breach-active tickets first, earliest breach first (TD-007/AC-3), only while the
    tenant's flag is on (AC-14); then newest first. Returns (ticket, breach_active) pairs."""
    async with tenant_session(who.tenant_id) as s:
        escalating = await flags.is_enabled(s, flags.SLA_BREACH_ESCALATION)
        active = breach_active_at() if escalating else literal(FAR_FUTURE)
        q = select(Ticket, active.label("active_at"))
        if not is_staff(who):
            q = q.where(Ticket.requester_id == who.user_id)  # TD-003/AC-5
        if status:
            q = q.where(Ticket.status == status)
        if priority:
            q = q.where(Ticket.priority == priority)
        if assignee_id:
            q = q.where(Ticket.assignee_id == assignee_id)
        if cursor:
            c_active, c_created, c_number = _decode_cursor(cursor)
            q = q.where(
                or_(
                    active > c_active,
                    and_(
                        active == c_active,
                        tuple_(Ticket.created_at, Ticket.number) < tuple_(c_created, c_number),
                    ),
                )
            )
        q = q.order_by(active.asc(), Ticket.created_at.desc(), Ticket.number.desc()).limit(limit + 1)
        rows = [(t, at) for t, at in (await s.execute(q)).all()]
    page, more = rows[:limit], len(rows) > limit
    next_cursor = _encode_cursor(*page[-1]) if more else None
    return [(t, at != FAR_FUTURE) for t, at in page], next_cursor


def breach_view(ticket: Ticket, escalating: bool) -> dict[str, Any] | None:
    """The `breach` DTO field (TD-007 design section 6): the earliest breach, and whether it
    still needs action. History is always shown; `active` needs the flag on (AC-14)."""
    unresolved = ticket.status != "resolved"
    candidates = [
        ("first_response", ticket.first_response_breached_at, unresolved and ticket.first_replied_at is None),
        ("resolution", ticket.resolution_breached_at, unresolved),
    ]
    breached = [(at, kind, needs_action) for kind, at, needs_action in candidates if at is not None]
    if not breached:
        return None
    live = [b for b in breached if b[2]]
    at, kind, needs_action = min(live or breached)
    return {"type": kind, "breached_at": at, "active": escalating and needs_action}


async def breach_escalation_on(who: Principal) -> bool:
    async with tenant_session(who.tenant_id) as s:
        return await flags.is_enabled(s, flags.SLA_BREACH_ESCALATION)


async def _visible(s: AsyncSession, who: Principal, number: int, *, lock: bool = False) -> Ticket:
    q = select(Ticket).where(Ticket.number == number)
    if not is_staff(who):
        q = q.where(Ticket.requester_id == who.user_id)  # TD-003/AC-6
    if lock:
        q = q.with_for_update()
    ticket = (await s.execute(q)).scalar_one_or_none()
    if ticket is None:
        raise NOT_FOUND
    return ticket


async def get(who: Principal, number: int) -> tuple[Ticket, list[TicketMessage]]:
    async with tenant_session(who.tenant_id) as s:
        ticket = await _visible(s, who, number)
        q = select(TicketMessage).where(TicketMessage.ticket_id == ticket.id)
        if not is_staff(who):
            q = q.where(TicketMessage.kind == "public")  # TD-004/AC-3
        messages = list((await s.execute(q.order_by(TicketMessage.created_at))).scalars())
        return ticket, messages


async def add_message(who: Principal, number: int, data: MessageIn) -> TicketMessage:
    if data.internal and not is_staff(who):
        raise ProblemError(403, "Forbidden", "Only staff can add internal notes.")
    async with tenant_session(who.tenant_id) as s:
        ticket = await _visible(s, who, number, lock=True)
        message = TicketMessage(
            tenant_id=who.tenant_id,
            ticket_id=ticket.id,
            author_id=who.user_id,
            kind="internal" if data.internal else "public",
            body=data.body,
        )
        s.add(message)
        if is_staff(who) and not data.internal:
            if ticket.first_replied_at is None:
                ticket.first_replied_at = func.now()  # TD-004/AC-2
            await _set_status(s, who, ticket, workflow.after_staff_activity(ticket.status))
        elif not is_staff(who):
            await _set_status(s, who, ticket, workflow.after_customer_reply(ticket.status))  # AC-4
        await s.flush()
        await s.refresh(message)
        return message


async def update(who: Principal, number: int, change: TicketPatchIn) -> Ticket:
    if not is_staff(who):
        raise STAFF_ONLY
    fields = change.model_fields_set
    async with tenant_session(who.tenant_id) as s:
        ticket = await _visible(s, who, number, lock=True)
        target = change.status if "status" in fields else None
        if (
            target is not None
            and target != ticket.status
            and not workflow.staff_can_move(ticket.status, target)
        ):
            # Checked against the status BEFORE this request's other changes (an assignment
            # also moves new -> open; {assignee_id, status: "open"} must not then fail).
            raise ProblemError(409, "Invalid transition", f"Can't move from {ticket.status} to {target}.")
        if "assignee_id" in fields and change.assignee_id != ticket.assignee_id:
            if change.assignee_id is not None and not await _user_with_role(
                s, change.assignee_id, STAFF_ROLES
            ):
                raise ProblemError(
                    422, "Invalid assignee", "Assign to an active staff member of this tenant."
                )
            await _audit_change(s, who, ticket, "assignee", ticket.assignee_id, change.assignee_id)
            ticket.assignee_id = change.assignee_id
            if change.assignee_id not in (None, who.user_id):  # TD-006/AC-5; no self-notify
                await notify(
                    s,
                    who.tenant_id,
                    [change.assignee_id],
                    "ticket_assigned",
                    ticket.id,
                    {"number": ticket.number, "subject": ticket.subject},
                    # Unique per assignment: each (re)assignment is news, so no dedupe here.
                    f"assigned:{ticket.id}:{uuid.uuid4().hex}",
                )
            await _set_status(s, who, ticket, workflow.after_staff_activity(ticket.status))
        for field in ("priority", "category"):
            new = getattr(change, field)
            if field in fields and new != getattr(ticket, field) and (field == "category" or new is not None):
                await _audit_change(s, who, ticket, field, getattr(ticket, field), new)
                setattr(ticket, field, new)
                if field == "priority":
                    _recompute_deadlines(ticket)
        if target is not None:
            await _set_status(s, who, ticket, target)  # no-op when already there
        await s.flush()
        await s.refresh(ticket)
        return ticket
