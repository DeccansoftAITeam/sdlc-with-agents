"""HTTP routes for TD-003 / TD-004. No business logic here (AGENTS.md)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.errors import ProblemError
from app.core.security import Principal, current_principal
from app.features.tickets import service
from app.features.tickets.schemas import (
    MessageIn,
    MessageOut,
    Priority,
    Status,
    TicketCreateIn,
    TicketDetailOut,
    TicketOut,
    TicketPage,
    TicketPatchIn,
)
from app.features.users.service import current_role

router = APIRouter(tags=["tickets"])


async def member(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
    """Use the role as it is NOW in the database, not as it was when the token was issued."""
    role = await current_role(principal)
    if role is None:
        raise ProblemError(403, "Forbidden", "Account deactivated.")
    return Principal(principal.user_id, principal.tenant_id, role)


Member = Annotated[Principal, Depends(member)]


def _out(model: type[TicketOut], obj: object, **extra: object) -> TicketOut:
    return model.model_validate({**{k: getattr(obj, k) for k in TicketOut.model_fields}, **extra})


@router.post("/t/{slug}/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(slug: str, body: TicketCreateIn, who: Member) -> TicketOut:
    return _out(TicketOut, await service.create(who, body))


@router.get("/t/{slug}/tickets")
async def list_tickets(
    slug: str,
    who: Member,
    status_: Annotated[Status | None, Query(alias="status")] = None,
    priority: Priority | None = None,
    assignee_id: uuid.UUID | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TicketPage:
    items, next_cursor = await service.queue(
        who, status=status_, priority=priority, assignee_id=assignee_id, cursor=cursor, limit=limit
    )
    return TicketPage(items=[_out(TicketOut, t) for t in items], next_cursor=next_cursor)


@router.get("/t/{slug}/tickets/{number}")
async def get_ticket(slug: str, number: int, who: Member) -> TicketDetailOut:
    # The return annotation IS the response model: annotating TicketOut here silently
    # dropped `messages` from the response (caught by the AC-3 acceptance test).
    ticket, messages = await service.get(who, number)
    msgs = [MessageOut.model_validate(m, from_attributes=True) for m in messages]
    detail = _out(TicketDetailOut, ticket, messages=msgs)
    assert isinstance(detail, TicketDetailOut)
    return detail


@router.post("/t/{slug}/tickets/{number}/messages", status_code=status.HTTP_201_CREATED)
async def add_message(slug: str, number: int, body: MessageIn, who: Member) -> MessageOut:
    return MessageOut.model_validate(await service.add_message(who, number, body), from_attributes=True)


@router.patch("/t/{slug}/tickets/{number}")
async def update_ticket(slug: str, number: int, body: TicketPatchIn, who: Member) -> TicketOut:
    return _out(TicketOut, await service.update(who, number, body))
