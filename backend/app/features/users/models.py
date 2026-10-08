"""Users live in the auth feature (TD-001). This module registers the shared audit table
with the ORM metadata, so Alembic and the models-vs-migrations test see it."""

from app.core.audit import AuditEntry

__all__ = ["AuditEntry"]
