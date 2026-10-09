"""HTTP routes for TD-006. No business logic here (AGENTS.md)."""

import uuid

from fastapi import APIRouter, status

from app.features.notifications import service
from app.features.notifications.schemas import Inbox, NotificationOut
from app.features.users.deps import Member

router = APIRouter(tags=["notifications"])


@router.get("/t/{slug}/notifications")
async def list_notifications(slug: str, who: Member) -> Inbox:
    items, unread = await service.inbox(who)
    return Inbox(
        items=[NotificationOut.model_validate(n, from_attributes=True) for n in items], unread_count=unread
    )


@router.post("/t/{slug}/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(slug: str, who: Member) -> None:
    await service.mark_read(who, None)


@router.post("/t/{slug}/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(slug: str, notification_id: uuid.UUID, who: Member) -> None:
    await service.mark_read(who, notification_id)
