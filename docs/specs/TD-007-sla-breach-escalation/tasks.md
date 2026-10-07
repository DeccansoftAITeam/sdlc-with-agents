# Tasks: TD-007 Escalate ticket on SLA breach

| Field | Value |
|---|---|
| Spec | ./spec.md |
| Design | ./design.md |
| Status | **Draft: awaiting Tech Lead approval** |
| Prerequisites | TD-005 and TD-006 merged |

## Task index

| Task ID | Title | Depends on | Mode | Risk tier | Status |
|---|---|---|---|---|---|
| T-007-01 | Migration: breach columns + partial indexes | — | M2 | **High** (migration) | Todo |
| T-007-02 | Sweep service + worker entry point | T-007-01 | M2 | Medium | Todo |
| T-007-03 | Queue ordering + breach fields in API | T-007-01 | M2 | Medium | Todo |
| T-007-04 | Web: breach badge + queue order | T-007-03 | M2 | Medium | Todo |
| T-007-05 | Metrics + feature flag wiring | T-007-02 | M1 | Low | Todo |

T-007-02 and T-007-03 can run **in parallel**, for example Claude Code on one and Copilot on the other, each in its own `treehouse` worktree.

---

## T-007-01: Migration: breach columns + partial indexes

| Field | Value |
|---|---|
| Goal | Expand-only migration adding the breach columns, partial indexes and notification unique constraint from design §3 |
| Acceptance criteria covered | none directly (enables AC-1, AC-2, AC-7) |
| Mode | M2 Delegated, skill **`migration-writer`** |
| Change-risk tier | **High**: 2 approvals including TL |
| Branch | `agent/T-007-01-breach-columns` |
| Budget | 60 steps · 30 min · 500k tokens |

**Files in scope:** `backend/app/features/tickets/models.py`, `backend/app/features/notifications/models.py`, `backend/migrations/versions/*_td007_*.py`, `backend/tests/migrations/test_td007_*.py`

**Out of scope:** any service, router or web code.

**Done criteria**
- [ ] `upgrade → downgrade → upgrade` passes against the test container
- [ ] Indexes created `CONCURRENTLY`; `squawk` clean
- [ ] Existing RLS policies untouched; `test_rls_blocks_cross_tenant_select` still passes
- [ ] Local gate passes; draft PR with agent attribution

---

## T-007-02: Sweep service + worker entry point

| Field | Value |
|---|---|
| Goal | Implement design §4: the sweep, run every 30 s by `python -m app.workers.main` |
| Acceptance criteria covered | AC-1, AC-2, AC-4, AC-5, AC-6, AC-7, AC-8, AC-10, AC-14 |
| Mode | M2 Delegated, skill **`acceptance-tdd`** |
| Change-risk tier | Medium |
| Branch | `agent/T-007-02-sla-sweep` |
| Budget | 200 steps · 60 min · 2M tokens |

**Inputs:** spec §3–4, design §4, ADR-0003, `backend/app/core/db.py` (tenant session helper), TD-005 `compute_deadlines`

**Files in scope:** `backend/app/features/sla/sweep.py`, `backend/app/workers/**`, `backend/tests/features/sla/test_sweep.py`, `backend/tests/conftest.py` (fixtures only)

**Out of scope:** migrations, auth, `compute_deadlines` itself (TD-005), web.

**Done criteria**
- [ ] **Phase A:** acceptance tests for every listed AC written first, failing for the right reason, **human-reviewed** before implementing
- [ ] Concurrency test: two sweeps in parallel → one notification per user (AC-7)
- [ ] Cross-tenant test (AC-8) and flag-off test (AC-14)
- [ ] Uses DB `now()` only; frozen clock in tests
- [ ] Local gate passes; draft PR

---

## T-007-03: Queue ordering + breach fields in API

| Field | Value |
|---|---|
| Goal | Order the queue by breach-active (design §5) and expose `breach` on ticket DTOs |
| Acceptance criteria covered | AC-3, AC-12, AC-8 (queue side) |
| Mode | M2 Delegated, skill **`acceptance-tdd`** |
| Change-risk tier | Medium |
| Branch | `agent/T-007-03-queue-order` |
| Budget | 120 steps · 45 min · 1M tokens |

**Files in scope:** `backend/app/features/tickets/{queries,schemas,router}.py`, `backend/tests/features/tickets/test_queue.py`, `packages/core/src/generated/**` (regenerated client only)

**Done criteria**
- [ ] Acceptance tests first, human-reviewed
- [ ] OpenAPI change is additive (`oasdiff` shows no breaking change); client regenerated
- [ ] Local gate passes; draft PR

---

## T-007-04: Web: breach badge + queue order

| Field | Value |
|---|---|
| Goal | Show the breach badge (AC-9) and render the API's order (AC-3) |
| Acceptance criteria covered | AC-3 (E2E), AC-9 |
| Mode | M2 Delegated, skill **`acceptance-tdd`** (Playwright first) |
| Change-risk tier | Medium |
| Branch | `agent/T-007-04-breach-badge` |
| Budget | 120 steps · 45 min · 1M tokens |

**Files in scope:** `apps/web/src/features/queue/**`, `apps/web/e2e/queue.spec.ts`

**Done criteria**
- [ ] Badge has a text label ("First response breached 2h ago"), not colour alone; axe shows no serious or critical issues
- [ ] Badge hidden once breach is no longer active (AC-12)
- [ ] Local gate passes; draft PR

---

## T-007-05: Metrics + feature flag wiring

| Field | Value |
|---|---|
| Goal | Emit the design §11 metrics; read the `sla-breach-escalation` flag per tenant |
| Acceptance criteria covered | AC-14 (flag), SLO instrumentation |
| Mode | **M1 Pair** (small, touches telemetry config) |
| Change-risk tier | Low |
| Branch | `feat/TD-007-metrics` |
| Budget | — |

**Files in scope:** `backend/app/features/sla/metrics.py`, `backend/app/core/flags.py`, related tests

**Done criteria**
- [ ] Metrics visible at `/metrics` locally; no PII in labels
- [ ] Local gate passes; PR

---

## Approval

> 🎩 **Tech Lead:** approving this file authorises agents to run T-007-01…04 in M2, limited to the listed files and budgets.

| Role | Name | Date |
|---|---|---|
| Tech Lead | | |
| Product Owner (spec) | | |
