# Tasks: Foundations TD-001 … TD-006

| Field | Value |
|---|---|
| Specs | `TD-001` … `TD-006` folders |
| Status | **Approved** (2026-10-07) |
| Prerequisite | M3 scaffold merged (`m03-done`) |

Shared rules for every task: branch `agent/<task-id>-<slug>`; acceptance tests first and human-reviewed (`acceptance-tdd`); a cross-tenant test for every endpoint; PR of about 400 lines or fewer; local gate green; draft PR with agent attribution. **High**-tier tasks need 2 approvals including the TL plus a `security-reviewer` pass.

| Task | Spec ACs | Mode · skill | Tier | Files in scope | Budget | Depends on |
|---|---|---|---|---|---|---|
| T-001-01 Tenant + user + token tables, RLS | — | M2 · `migration-writer` | **High** | `backend/app/features/auth/models.py`, `backend/migrations/versions/*_td001_*`, `backend/tests/migrations/` | 60 steps · 30 min | M3 |
| T-001-02 Signup + verification + email port | TD-001/AC-1,2,3,7,9,11 | M2 · `acceptance-tdd` | **High** | `backend/app/features/auth/{signup,verify,email}*.py`, `backend/app/core/email.py`, `backend/tests/features/auth/test_signup*.py` | 200 · 60 min | T-001-01 |
| T-001-03 Login, JWT, refresh rotation, rate limits | TD-001/AC-4,5,6,7,8,12 | **M1** · `acceptance-tdd` | **High** | `backend/app/features/auth/{login,tokens,ratelimit}*.py`, `backend/app/core/security.py`, `backend/app/core/tenancy.py`, tests | — | T-001-02 |
| T-001-04 Password reset | TD-001/AC-7,9,10 | M2 · `acceptance-tdd` | **High** | `backend/app/features/auth/reset*.py`, tests | 120 · 45 min | T-001-03 |
| T-001-05 Web: signup, login, verify, reset pages | TD-001 E2E | M2 · `acceptance-tdd` | Medium | `apps/web/src/app/(auth)/**`, `apps/web/src/app/t/[slug]/(auth)/**`, `apps/web/e2e/auth.spec.ts` | 150 · 60 min | T-001-04 |
| T-002-01 Roles, invites, customer registration, audit helper | TD-002/AC-1…8 | M2 · `acceptance-tdd` (+ `migration-writer` for the invites table) | **High** | `backend/app/features/users/**`, `backend/app/core/audit.py`, `backend/migrations/versions/*_td002_*`, tests | 200 · 60 min | T-001-03 |
| T-003-01 Tickets model, create, queue, view API | TD-003/AC-1…6,8 | M2 · `acceptance-tdd` | Medium | `backend/app/features/tickets/**`, `backend/migrations/versions/*_td003_*`, tests, `packages/core/src/generated/**` | 200 · 60 min | T-002-01 |
| T-003-02 Web: create, queue, view (sanitized markdown) | TD-003/AC-7,9 | M2 · `acceptance-tdd` | Medium | `apps/web/src/features/tickets/**`, `apps/web/e2e/tickets.spec.ts` | 150 · 60 min | T-003-01 |
| T-004-01 Messages, notes, status machine, assignment, audit | TD-004/AC-1…6,8 | M2 · `acceptance-tdd` | Medium | `backend/app/features/tickets/{workflow,messages}*.py`, migration `*_td004_*`, tests | 200 · 60 min | T-003-01 |
| T-005-01 `compute_deadlines` (pure, property-based) | TD-005/AC-3…6 | **M1** · `acceptance-tdd` | Medium | `backend/app/features/sla/deadlines.py`, `backend/tests/features/sla/test_deadlines.py` | — | M3 |
| T-005-02 SLA settings + deadline storage + recompute hooks | TD-005/AC-1,2,7; TD-004/AC-7 | M2 · `acceptance-tdd` | Medium | `backend/app/features/sla/{settings,service}.py`, migration `*_td005_*`, tests | 200 · 60 min | T-004-01, T-005-01 |
| T-006-01 Notifications API + `notify()` + retention | TD-006/AC-1,2,3,5,6,7 | M2 · `acceptance-tdd` | Low | `backend/app/features/notifications/**`, migration `*_td006_*`, tests | 150 · 45 min | T-002-01 |
| T-006-02 Web: bell + unread count | TD-006/AC-4 | M2 · `acceptance-tdd` | Low | `apps/web/src/features/notifications/**`, `apps/web/e2e/notifications.spec.ts` | 100 · 30 min | T-006-01 |

**Parallel lanes** (one per harness, each in its own `treehouse` worktree):
- Lane A (Claude Code): T-001-* → T-002-01 → T-003-01 → T-004-01 → T-005-02
- Lane B (Copilot): T-005-01 (no dependencies) → T-006-01 (after T-002-01) → web tasks

**Why T-001-03 and T-005-01 are M1 (Pair), not M2:** token handling and the deadline maths are where subtle bugs hide. A human drives these interactively instead of reviewing a finished PR.

## Approval

| Role | Name | Date |
|---|---|---|
| Tech Lead | DeccansoftAITeam | 2026-10-07 |
| Product Owner (specs) | DeccansoftAITeam | 2026-10-07 |
