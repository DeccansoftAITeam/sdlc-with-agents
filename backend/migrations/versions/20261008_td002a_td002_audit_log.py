"""td002 audit log

Revision ID: td002a
Revises: td001a
Create Date: 2026-10-08
Phase: expand (new table only)
Task: T-002-01 / PR B (TD-002/AC-7; TM-008)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from migrations.rls import enable_rls

revision: str = "td002a"
down_revision: str | None = "td001a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _app_role() -> str:
    """The runtime role. Fails loudly instead of silently revoking from the wrong role."""
    from sqlalchemy.engine import make_url

    from app.core.config import get_settings

    settings = get_settings()
    app = make_url(settings.database_url).username
    owner = make_url(settings.migration_database_url).username
    if not app or app == owner:
        raise RuntimeError("database_url must use a runtime role distinct from the migration owner")
    return app


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_log_tenant_id"), "audit_log", ["tenant_id"], unique=False)
    op.create_index("ix_audit_log_entity", "audit_log", ["tenant_id", "entity_id"])
    # Added by hand (autogenerate emits neither): tenant isolation + append-only.
    enable_rls("audit_log")
    op.execute(f'REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM "{_app_role()}"')


def downgrade() -> None:
    op.drop_index("ix_audit_log_entity", table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_tenant_id"), table_name="audit_log")
    op.drop_table("audit_log")
