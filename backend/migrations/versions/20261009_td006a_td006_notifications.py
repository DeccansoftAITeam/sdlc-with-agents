"""td006 notifications

Revision ID: td006a
Revises: td005a
Create Date: 2026-10-09 08:18:55
Phase: expand (new table only)
Task: PR D (TD-006)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from migrations.rls import enable_rls

revision: str = "td006a"
down_revision: str | None = "td005a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("dedupe_key", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "ticket_id"], ["tickets.tenant_id", "tickets.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"], ["users.tenant_id", "users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "dedupe_key", name="uq_notifications_dedupe"),
    )
    op.create_index(
        "ix_notifications_inbox", "notifications", ["tenant_id", "user_id", "created_at"], unique=False
    )
    op.create_index(op.f("ix_notifications_tenant_id"), "notifications", ["tenant_id"], unique=False)
    # Added by hand: autogenerate never emits RLS (migration-writer skill, step 4).
    enable_rls("notifications")


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_tenant_id"), table_name="notifications")
    op.drop_index("ix_notifications_inbox", table_name="notifications")
    op.drop_table("notifications")
