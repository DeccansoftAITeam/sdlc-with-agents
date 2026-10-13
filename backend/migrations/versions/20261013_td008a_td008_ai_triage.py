"""td008 ai triage tables

Revision ID: td008a
Revises: td007a
Create Date: 2026-10-13 14:00:00
Phase: expand (new tables only)
Task: T-008-02 (TD-008)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from migrations.rls import enable_rls

revision: str = "td008a"
down_revision: str | None = "td007a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = sa.text("now()")


def _ticket_fk() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        ["tenant_id", "ticket_id"], ["tickets.tenant_id", "tickets.id"], ondelete="CASCADE"
    )


def upgrade() -> None:
    op.create_table(
        "ai_triage_jobs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'queued'"), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("paused_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        _ticket_fk(),
        sa.CheckConstraint(
            "status IN ('queued', 'paused', 'done', 'failed')", name="ck_ai_triage_jobs_status"
        ),
    )
    op.create_index("ix_ai_triage_jobs_tenant_id", "ai_triage_jobs", ["tenant_id"])
    op.create_index(
        "ix_ai_triage_jobs_queued",
        "ai_triage_jobs",
        ["created_at"],
        postgresql_where=sa.text("status = 'queued'"),
    )

    op.create_table(
        "ai_suggestions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("decided_by", sa.UUID(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        _ticket_fk(),
        sa.UniqueConstraint("tenant_id", "ticket_id", name="uq_ai_suggestions_ticket"),
        sa.CheckConstraint(
            "decision IN ('pending', 'accepted', 'overridden')", name="ck_ai_suggestions_decision"
        ),
    )
    op.create_index("ix_ai_suggestions_tenant_id", "ai_suggestions", ["tenant_id"])

    op.create_table(
        "ai_usage",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("output_tokens", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("requests", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "month", name="pk_ai_usage"),
    )
    op.create_index("ix_ai_usage_tenant_id", "ai_usage", ["tenant_id"])

    # Added by hand: autogenerate never emits RLS (migration-writer skill, step 4).
    for table in ("ai_triage_jobs", "ai_suggestions", "ai_usage"):
        enable_rls(table)


def downgrade() -> None:
    op.drop_table("ai_usage")
    op.drop_table("ai_suggestions")
    op.drop_table("ai_triage_jobs")
