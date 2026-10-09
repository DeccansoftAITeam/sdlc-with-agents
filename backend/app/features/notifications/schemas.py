import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    kind: str
    ticket_id: uuid.UUID | None
    payload: dict[str, Any]
    read_at: datetime | None
    created_at: datetime


class Inbox(BaseModel):
    items: list[NotificationOut]
    unread_count: int
