"""TD-003 / TD-004 services. Every query runs in the caller's tenant RLS session.

Visibility rules: staff and admins see every ticket of their tenant; customers see only
tickets they requested, and never internal notes. A ticket a caller may not see is a
404, never a 403, so its existence isn't revealed (TD-003/AC-6).
"""

import base64
import binascii
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.db import tenant_session
from app.core.errors import ProblemError
from app.core.security import Principal
from app.features.auth.models import Role, User
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


async def _set_status(s: AsyncSession, who: Principal, ticket: Ticket, new: str) -> None:
    if new == ticket.status:
        return
    await _audit_change(s, who, ticket, "status", ticket.status, new)
    ticket.status = new
    ticket.resolved_at = func.now() if new == "resolved" else None


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
        )
        s.add(ticket)
        await s.flush()
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


def _encode_cursor(t: Ticket) -> str:
    return base64.urlsafe_b64encode(f"{t.created_at.isoformat()}|{t.number}".encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        created, number = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return datetime.fromisoformat(created), int(number)
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
) -> tuple[list[Ticket], str | None]:
    q = select(Ticket)
    if not is_staff(who):
        q = q.where(Ticket.requester_id == who.user_id)  # TD-003/AC-5
    if status:
        q = q.where(Ticket.status == status)
    if priority:
        q = q.where(Ticket.priority == priority)
    if assignee_id:
        q = q.where(Ticket.assignee_id == assignee_id)
    if cursor:
        q = q.where(tuple_(Ticket.created_at, Ticket.number) < tuple_(*_decode_cursor(cursor)))
    q = q.order_by(Ticket.created_at.desc(), Ticket.number.desc()).limit(limit + 1)
    async with tenant_session(who.tenant_id) as s:
        rows = list((await s.execute(q)).scalars())
    page, more = rows[:limit], len(rows) > limit
    return page, (_encode_cursor(page[-1]) if more else None)


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
        if "assignee_id" in fields and change.assignee_id != ticket.assignee_id:
            if change.assignee_id is not None and not await _user_with_role(
                s, change.assignee_id, STAFF_ROLES
            ):
                raise ProblemError(
                    422, "Invalid assignee", "Assign to an active staff member of this tenant."
                )
            await _audit_change(s, who, ticket, "assignee", ticket.assignee_id, change.assignee_id)
            ticket.assignee_id = change.assignee_id
            await _set_status(s, who, ticket, workflow.after_staff_activity(ticket.status))
        for field in ("priority", "category"):
            new = getattr(change, field)
            if field in fields and new != getattr(ticket, field) and (field == "category" or new is not None):
                await _audit_change(s, who, ticket, field, getattr(ticket, field), new)
                setattr(ticket, field, new)
        if "status" in fields and change.status is not None:
            if not workflow.staff_can_move(ticket.status, change.status):
                raise ProblemError(
                    409, "Invalid transition", f"Can't move from {ticket.status} to {change.status}."
                )
            await _set_status(s, who, ticket, change.status)
        await s.flush()
        await s.refresh(ticket)
        return ticket
