"""Outbound email port (constitution: auth email only, via Azure Communication Services).

Domain code depends on `EmailSender`; the ACS adapter lives in app/adapters/ (added with
the deploy work, M9). Locally and in tests the in-memory outbox is used. Never log
recipients or bodies: they contain personal data and live tokens.
"""

import logging
from dataclasses import dataclass, field
from typing import Protocol

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailSender(Protocol):
    async def send(self, message: EmailMessage) -> None: ...


@dataclass
class InMemoryOutbox:
    """Collects messages instead of sending them (local development and tests)."""

    messages: list[EmailMessage] = field(default_factory=list)

    async def send(self, message: EmailMessage) -> None:
        self.messages.append(message)
        log.info("email queued in local outbox", extra={"subject": message.subject})


_default_sender = InMemoryOutbox()


def get_email_sender() -> EmailSender:
    """FastAPI dependency. Production wiring replaces this with the ACS adapter."""
    return _default_sender
