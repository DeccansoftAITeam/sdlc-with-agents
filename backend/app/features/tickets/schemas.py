import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Status = Literal["new", "open", "pending_customer", "resolved"]
Priority = Literal["P1", "P2", "P3", "P4"]
Category = Literal["billing", "technical", "account", "other"]


class TicketCreateIn(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)
    priority: Priority | None = None  # staff only (TD-003/AC-3)
    category: Category | None = None  # staff only
    requester_id: uuid.UUID | None = None  # required when staff create on behalf (AC-2)


class TicketPatchIn(BaseModel):
    """Only fields present in the request are changed (`model_fields_set`)."""

    status: Status | None = None
    priority: Priority | None = None
    category: Category | None = None  # null clears the category
    assignee_id: uuid.UUID | None = None  # null unassigns

    @model_validator(mode="after")
    def _no_null_status_or_priority(self) -> "TicketPatchIn":
        for field in ("status", "priority"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} can't be null")
        return self


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)
    internal: bool = False


class MessageOut(BaseModel):
    author_id: uuid.UUID
    kind: str
    body: str
    created_at: datetime


class TicketOut(BaseModel):
    id: uuid.UUID
    number: int
    subject: str
    status: str
    priority: str
    category: str | None
    requester_id: uuid.UUID
    assignee_id: uuid.UUID | None
    first_replied_at: datetime | None
    resolved_at: datetime | None
    first_response_due_at: datetime | None
    resolution_due_at: datetime | None
    created_at: datetime


class TicketDetailOut(TicketOut):
    messages: list[MessageOut]


class TicketPage(BaseModel):
    items: list[TicketOut]
    next_cursor: str | None
