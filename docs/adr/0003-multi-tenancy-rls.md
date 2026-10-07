# ADR-0003: Shared database, `tenant_id` + Postgres row-level security, path-slug routing

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-07 |
| Deciders | Tech Lead |
| Consulted | Security reviewer |
| Deviates from org default? | No |
| Related spec(s) | All |

## Context and problem statement

TicketDesk is a self-serve multi-tenant SaaS (grill Q1). Constitution principle 1: *tenant isolation is absolute and enforced by the database, not just application code.* Cross-tenant read (TM-003) is the top threat. We need an isolation model that survives a forgotten `WHERE` clause.

## Decision drivers

- Defence in depth: a missing filter in code must not leak data
- Cost: up to hundreds of small free tenants
- Background jobs (SLA sweep, TD-007) must respect isolation too

## Considered options

1. Database per tenant
2. Schema per tenant
3. **Shared tables with `tenant_id` + RLS**
4. Shared tables with `tenant_id` filtered in application code only

## Decision outcome

**Option 3.**

- Every tenant-owned table has `tenant_id uuid NOT NULL` and **`ENABLE` + `FORCE ROW LEVEL SECURITY`** with the policy `USING (tenant_id = current_setting('app.tenant_id')::uuid)` (also `WITH CHECK`).
- The app connects as role `ticketdesk_app`: **not the table owner, and no `BYPASSRLS`**. Migrations run as a separate owner role.
- Each request opens a transaction and runs `SET LOCAL app.tenant_id = <tid from JWT>`. If the setting is missing, the policy matches nothing (fails closed).
- **Routing:** tenants appear in URLs as `/t/{slug}`. Middleware resolves the slug; **if it doesn't match the JWT's `tid`, respond 404** (grill Q3). Slugs are unique and immutable; reserved words are blocked.
- **Background jobs** (e.g. the SLA sweep) loop over tenants and set `app.tenant_id` per iteration. **No job uses a bypass role.**
- Tables that aren't tenant-owned (`tenants` itself) are only accessed through narrow, tested functions.

### Consequences

- Good: a forgotten filter returns nothing instead of another tenant's rows.
- Good: one database, cheap at our scale.
- Bad: every query and job must run inside a tenant-scoped transaction, which needs one well-tested session helper.
- Bad: per-tenant loops scale linearly. Fine to about 1k tenants (TD-007 NFR), then revisit.

### Confirmation

- `test_rls_blocks_cross_tenant_select` runs directly against Postgres as `ticketdesk_app` without `app.tenant_id` → 0 rows.
- Architecture test: every model with `tenant_id` has a migration that enables and forces RLS (conformance in M8).
- A cross-tenant API test for every endpoint (`acceptance-tdd` skill rule).
- `test_slug_jwt_mismatch_returns_404`.
