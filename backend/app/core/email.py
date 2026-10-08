"""Outbound email port (constitution: auth email only, via Azure Communication Services).

Domain code depends on `EmailSender`; the ACS adapter lives in app/adapters/ (added with
the deploy work, M9). Locally and in tests the in-memory outbox is used. Never log
recipients or bodies: they contain personal data and live tokens.
"""

import logging
from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import get_settings

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


_local_outbox = InMemoryOutbox()


def get_email_sender() -> EmailSender:
    """FastAPI dependency. The in-memory outbox is allowed ONLY when environment=local;
    anywhere else, a missing real sender is a configuration error, never a silent no-op."""
    settings = get_settings()
    if settings.email_backend == "outbox" and settings.environment == "local":
        return _local_outbox
    raise RuntimeError(
        f"email_backend={settings.email_backend!r} is not available in environment={settings.environment!r}"
    )
