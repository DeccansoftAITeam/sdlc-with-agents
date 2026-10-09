"""td005 SLA settings and ticket deadlines

Revision ID: td005a
Revises: td003a
Create Date: 2026-10-09 08:18:55
Phase: expand (new table + nullable/defaulted columns only)
Task: PR D (TD-005)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from migrations.rls import enable_rls

revision: str = "td005a"
down_revision: str | None = "td003a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_sla_settings",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("targets", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("schedule", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_sla_settings_tenant"),
    )
    op.create_index(
        op.f("ix_tenant_sla_settings_tenant_id"), "tenant_sla_settings", ["tenant_id"], unique=False
    )
    # Added by hand: autogenerate never emits RLS (migration-writer skill, step 4).
    enable_rls("tenant_sla_settings")

    op.add_column("tickets", sa.Column("sla_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(
        "tickets",
        sa.Column(
            "paused_intervals",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column("tickets", sa.Column("first_response_due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tickets", sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "resolution_due_at")
    op.drop_column("tickets", "first_response_due_at")
    op.drop_column("tickets", "paused_intervals")
    op.drop_column("tickets", "sla_policy")
    op.drop_index(op.f("ix_tenant_sla_settings_tenant_id"), table_name="tenant_sla_settings")
    op.drop_table("tenant_sla_settings")
