# Tasks: Foundations TD-001 … TD-006

| Field | Value |
|---|---|
| Specs | `TD-001` … `TD-006` folders |
| Status | **Approved** (2026-10-07) |
| Prerequisite | M3 scaffold merged (`m03-done`) |

Shared rules for every task: branch `agent/<task-id>-<slug>`; acceptance tests first and human-reviewed (`acceptance-tdd`); a cross-tenant test for every endpoint; PR of about 400 lines or fewer; local gate green; draft PR with agent attribution. **High**-tier tasks need 2 approvals including the TL plus a `security-reviewer` pass.

| Task | Spec ACs | Mode · skill | Tier | Files in scope | Budget | Depends on |
|---|---|---|---|---|---|---|
| T-001-01 Tenant + user + token tables, RLS | — | M2 · `migration-writer` | **High** | `backend/app/features/auth/{__init__,models}.py`, `backend/migrations/versions/*_td001_*`, `backend/tests/migrations/**` | 60 steps · 30 min | M3 |
| T-001-02 Signup + password policy | TD-001/AC-1,2,3 | M2 · `acceptance-tdd` | **High** | `backend/app/features/auth/{signup,router,schemas,passwords,service}*.py`, `backend/app/features/auth/common_passwords.txt`, `backend/app/main.py`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/tests/conftest.py`, `backend/tests/features/**` | 200 · 60 min | T-001-01 |
| **A** T-001-03 Login, JWT, refresh rotation, rate limits | TD-001/AC-4,5,6,7,8,12 | M2 · `acceptance-tdd` | **High** | `backend/app/core/{security,ratelimit,config}.py`, `backend/app/features/auth/**`, `backend/app/main.py`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/tests/**`, `docs/specs/**` | 200 · 60 min | T-001-02 |
| **B** T-002-01 Roles + customer registration (minimal) | TD-002/AC-3,4,5,6,7,8,10 | M2 · `acceptance-tdd` | **High** | `backend/app/features/users/**`, `backend/app/core/audit.py`, `backend/migrations/versions/*_td002_*`, `backend/app/main.py`, `backend/tests/**` | 200 · 60 min | A |
| **C** T-003/004 Tickets API + workflow + audit | TD-003/AC-1…6,8; TD-004/AC-1…6,8 | M2 · `acceptance-tdd` | Medium | `backend/app/features/tickets/**`, `backend/migrations/versions/*_td003_*`, `backend/app/main.py`, `backend/tests/**` | 200 · 60 min | B |
| **D** T-005/006 SLA clocks + notifications API | TD-005/AC-1…7; TD-006/AC-1,2,3,5,6,7; TD-004/AC-7 | M2 · `acceptance-tdd` | Medium | `backend/app/features/{sla,notifications}/**`, `backend/app/features/tickets/**`, `backend/migrations/versions/*_td00[56]_*`, `backend/app/main.py`, `backend/tests/**` | 200 · 60 min | C |
| → tag **`m04-start`** | | | | | | D |
| **E** TD-007 (all of `TD-007-*/tasks.md`) | TD-007/AC-1…14 | M2 · `acceptance-tdd` (+ `migration-writer`) | Medium | see TD-007 `tasks.md` | — | `m04-start` |


## Scope amendments

| Date | Task | Change | Why | Approved by |
|---|---|---|---|---|
| 2026-10-08 | T-001-01 | + `backend/app/features/auth/__init__.py`; `backend/tests/migrations/` → `backend/tests/migrations/**` | A feature package needs `__init__.py` or `load_models()` can't find its models; caught by the agent at task start (org rules §4: stop and ask) | TL, via PR review |
| 2026-10-08 | T-001-02 | + router, schemas, passwords, service modules; `main.py` (wire router); `core/config.py` (email + web URL settings); `pyproject.toml`/`uv.lock` (new deps: argon2-cffi, email-validator, httpx); `tests/conftest.py`; `tests/features/**` | The brief-grilled scope listed only the core modules; a feature needs routing, schemas, wiring and fixtures. Dependencies are proposed in this PR (org rules §3.6) | TL, via PR review |
| 2026-10-08 | T-001-02 → T-002-01 | TD-001/AC-11 (unverified admin can't invite or enable AI) moved | The guarded endpoints are built in T-002-01; testing a guard without its endpoint would be a fake test | TL, via PR review |
| 2026-10-08 | **All** | **Requirements change (PO): no email, no third-party services except AI.** T-001-02 reduced to signup + password policy (verification, email port, HIBP removed); T-001-04 removed; invites and resets become admin-issued links in T-002-01 (TD-002/AC-1, AC-9) | Keep the teaching project simple and self-contained | PO + TL, via PR review |
| 2026-10-08 | **All** | **Compressed for teaching (PO): the course is about the SDLC, not the product.** 16 remaining tasks → 5 PRs (A–E). Deferred to v2: invite/reset links (TD-002/AC-1,2,9; TD-001/AC-10) replaced by admins creating accounts directly (TD-002/AC-10); all web UI for TD-001…006 (T-001-05, T-003-02, T-006-02; TD-003/AC-7,9; TD-006/AC-4). A minimal web slice returns in M6 for E2E smoke. Learners build only TD-007 in the M4 lab, starting from `m04-start` | PO + TL, via PR A review |
| 2026-10-09 | D T-005/006 | + `backend/app/features/users/deps.py` (shared `member` dependency, moved from tickets); `backend/pyproject.toml`/`uv.lock` (new dep: `tzdata`, Apache-2.0, IANA timezone data for Windows and slim images); `docs/specs/TD-005-sla-clocks/spec.md` (implementation note) | A second feature needs `member` (PR C follow-up); `zoneinfo` has no timezone database on Windows; code review asked to record the AC-1 design | TL, via PR D review |

## Approval

| Role | Name | Date |
|---|---|---|
| Tech Lead | DeccansoftAITeam | 2026-10-07 |
| Product Owner (specs) | DeccansoftAITeam | 2026-10-07 |
