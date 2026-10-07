---
name: migration-writer
description: Writes a safe Alembic migration for PostgreSQL following expand → migrate → contract, with RLS policies for tenant tables and a squawk-clean SQL check. Use whenever a task changes the database schema.
---

# migration-writer (org skill · standard 2.0.0 · P3, high-risk tier)

Migrations are **high-risk** changes. They need two approvals, one of them the Tech Lead.

## Steps

0. If this runs as a `tasks.md` task, activate the scope guard first (same as `acceptance-tdd` Phase 0).

1. Update the SQLAlchemy models first. Then run `uv run alembic revision --autogenerate -m "<id>: <what>"`.
2. **Read the generated file and fix it.** Autogenerate misses renames, server defaults, enum changes and RLS.
3. Classify every operation:

| Kind | Examples | Allowed in this release? |
|---|---|---|
| Expand | add nullable column, add table, add index `CONCURRENTLY` | Yes |
| Migrate | backfill in batches | Yes, as a separate migration |
| Contract | drop column, add `NOT NULL`, rename | Only after the code no longer uses the old shape, **in a later release** |

Never put expand and contract steps in one release.

4. **Every new tenant-owned table** gets:
   - a `tenant_id uuid NOT NULL` column, with an index that leads with `tenant_id`
   - `ALTER TABLE … ENABLE ROW LEVEL SECURITY; ALTER TABLE … FORCE ROW LEVEL SECURITY;`
   - `CREATE POLICY tenant_isolation ON … USING (tenant_id = current_setting('app.tenant_id')::uuid);`
5. Create indexes on existing tables with `op.create_index(..., postgresql_concurrently=True)` inside an `autocommit_block()`.
6. Write a working `downgrade()`, or explain in the PR why the migration is irreversible.
7. Check it: `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` against the local test container, then `squawk` on the generated SQL (`alembic upgrade --sql`).

## Rules

- Never run migrations against any shared or remote database.
- Never edit a migration that is already merged. Write a new one.
