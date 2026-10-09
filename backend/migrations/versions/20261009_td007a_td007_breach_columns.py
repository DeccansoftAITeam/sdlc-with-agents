"""td007 breach columns, sweep indexes, per-tenant feature flags

Revision ID: td007a
Revises: td006a
Create Date: 2026-10-09 12:00:00
Phase: expand (nullable columns, new table, concurrent indexes)
Task: PR E (TD-007, T-007-01 + flag store for T-007-05)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import make_url

from migrations.rls import enable_rls

revision: str = "td007a"
down_revision: str | None = "td006a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _role(url_setting: str) -> str:
    from app.core.config import get_settings

    return make_url(getattr(get_settings(), url_setting)).username or "PUBLIC"


def upgrade() -> None:
    op.add_column(
        "tickets", sa.Column("first_response_breached_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("tickets", sa.Column("resolution_breached_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "feature_flags",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_feature_flags_tenant_key"),
    )
    op.create_index(op.f("ix_feature_flags_tenant_id"), "feature_flags", ["tenant_id"], unique=False)
    # Added by hand: autogenerate never emits RLS (migration-writer skill, step 4).
    enable_rls("feature_flags")

    # The sweep must find which tenants have a flag on BEFORE it can enter any tenant's
    # session (ADR-0003 per-tenant loop). One narrow SECURITY DEFINER function returns tenant
    # ids only, and the owner role may read just this table across tenants to serve it.
    owner, app = _role("migration_database_url"), _role("database_url")
    # flag_lookup is safe only while the app never logs in as the owner (security review).
    assert owner != app, "runtime and migration roles must differ (ADR-0003)"
    op.execute(f'CREATE POLICY flag_lookup ON feature_flags FOR SELECT TO "{owner}" USING (true)')
    op.execute(
        """
        CREATE FUNCTION tenants_with_flag(p_key text) RETURNS SETOF uuid
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS
        $$ SELECT tenant_id FROM feature_flags WHERE key = p_key AND enabled $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION tenants_with_flag(text) FROM PUBLIC")
    op.execute(f'GRANT EXECUTE ON FUNCTION tenants_with_flag(text) TO "{app}"')

    # Partial indexes for the sweep (design §3). CONCURRENTLY can't run in a transaction.
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_tickets_sla_due",
            "tickets",
            ["tenant_id", "first_response_due_at"],
            postgresql_where=sa.text("first_response_breached_at IS NULL AND first_replied_at IS NULL"),
            postgresql_concurrently=True,
        )
        op.create_index(
            "ix_tickets_res_due",
            "tickets",
            ["tenant_id", "resolution_due_at"],
            postgresql_where=sa.text(
                "resolution_breached_at IS NULL AND status NOT IN ('resolved', 'pending_customer')"
            ),
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("ix_tickets_res_due", table_name="tickets", postgresql_concurrently=True)
        op.drop_index("ix_tickets_sla_due", table_name="tickets", postgresql_concurrently=True)
    op.execute("DROP FUNCTION IF EXISTS tenants_with_flag(text)")
    op.drop_index(op.f("ix_feature_flags_tenant_id"), table_name="feature_flags")
    op.drop_table("feature_flags")
    op.drop_column("tickets", "resolution_breached_at")
    op.drop_column("tickets", "first_response_breached_at")
