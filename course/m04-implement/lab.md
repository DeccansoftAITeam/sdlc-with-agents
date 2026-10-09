# M4 Lab — Build TD-007 with agents

**Time:** about 4 h · **Starts at:** `m04-start` · **Reference solution:** `m04-done`
**Skills:** `acceptance-tdd`, `migration-writer`, `code-reviewer`, `security-reviewer` (M2 Delegated) · **Needs:** Docker running, a second GitHub account for approvals (M3)

> Read first: `docs/specs/TD-007-sla-breach-escalation/{spec,design,tasks}.md`. The tasks file is your permission slip. T-007-04 (web badge) is moved to M6; skip it.

## Step 0 — Start clean (10 min)

```sh
git fetch --tags && git switch -c lab/m04 m04-start
docker compose up -d db
cd backend && uv sync && uv run alembic upgrade head && uv run pytest -q   # 199 passed
```

If you see dozens of connection errors, Docker isn't running. Fix that before anything else.

## Step 1 — T-007-01: the migration (High tier, 45 min)

```
/migration-writer
Implement T-007-01 from docs/specs/TD-007-sla-breach-escalation/tasks.md.
Also add a per-tenant feature_flags table (forced RLS) and a narrow SECURITY DEFINER
function tenants_with_flag(key) returning tenant ids only: the sweep needs it (ADR-0003).
```

Check before you accept:

- [ ] `enable_rls("feature_flags")` is there. **Autogenerate leaves it out every time**; the architecture test fails without it
- [ ] Indexes use `postgresql_concurrently=True` and `if_not_exists=True` inside `autocommit_block()`
- [ ] The function has `SET search_path = public, pg_temp`, `REVOKE ALL … FROM PUBLIC`, one `GRANT EXECUTE` to the app role
- [ ] `uv run alembic downgrade td006a && uv run alembic upgrade head && uv run alembic check` → "No new upgrade operations"

**Puzzle:** both DB roles are `NOBYPASSRLS` and the table is `FORCE`d. Why does the SECURITY DEFINER function still return nothing, and what's the narrowest fix? (Answer in `m04-done:backend/migrations/versions/20261009_td007a_td007_breach_columns.py`.)

## Step 2 — T-007-02: the sweep, tests first (90 min)

```
/acceptance-tdd T-007-02
```

1. **Phase 0.** Open `.agents/progress/ACTIVE` and `T-007-02.md`. Now ask the agent to "also tidy up `app/core/security.py`". **The hook blocks it.** That's the gate, not the instruction, doing the work.
2. **Phase A.** The agent writes `tests/features/sla/test_sweep.py` and stops. 🎩 **You review the tests**, one per AC: 1, 2, 4, 5, 6, 7, 8, 10, 14. Insist on:
   - AC-7 with **two sweeps racing without the lock** (the lock is an optimisation; `UPDATE … WHERE breached_at IS NULL` is the guarantee)
   - AC-8 with two tenants, each seeing only its own notification
   - no `sleep`, no fake clock: move the stored deadline into the past
3. **Phase B.** Implementation. Compare with design §4: one `UPDATE … RETURNING` per SLA type, audit + `notify()` in the **same transaction**, dedupe key `breach:{ticket}:{type}`.
4. **Prove the tests bite:** replace `Ticket.first_response_breached_at.is_(None)` with `True`, rerun, and see AC-7 go red. Revert.

## Step 3 — T-007-03: the queue (45 min)

```
/acceptance-tdd T-007-03
```

The tricky part is pagination: the order is now *breach-active first (ASC), then newest first (DESC)*. A tuple comparison can't express mixed directions. Check the cursor test pages through with `limit=1` and gets **exactly** the unpaged order.

## Step 4 — Reviews (30 min)

Ask for both reviewers on the whole diff (High tier because of Step 1):

```
Use the code-reviewer and security-reviewer subagents on `git diff m04-start`.
```

Answer **every** finding: fix it with a test, or write down why not (deferred, accepted, out of scope) in your progress file. Our reviewers found, among others: reopened tickets resolved before the deploy breaching at once, and one bad tenant stalling the sweep for all the others. Did yours?

## Step 5 — PR (20 min)

```sh
uvx pre-commit run --hook-stage pre-push --all-files      # all Passed
git push -u origin agent/T-007-…
gh pr create --draft --fill
```

The PR must have: agent attribution trailers on every commit (`Agent-Model`, `Agent-Mode`, …), the scope-amendment rows you needed, review findings and their answers. 🎩 Switch to your reviewer account to approve; your own approval doesn't count (last-push rule).

## Step 6 — Run it for real (10 min)

```sh
cd backend
JWT_EPHEMERAL_KEY=true uv run uvicorn app.main:app &      # API
uv run python -m app.workers.main                          # worker: sweeps every 30 s
```

Sign up a tenant, turn the flag on (`PUT /t/{slug}/flags/sla-breach-escalation`), create a P1 ticket, and watch nothing happen for an hour. That's correct. Then do what the tests do: move its deadline into the past, and within 30 s the worker logs `sla sweep: 1 breaches`.

## Done when

- [ ] All TD-007 acceptance tests pass; full suite green, coverage ≥ 80%, squawk clean
- [ ] You saw the scope guard block an edit, and a deliberately broken sweep turn a test red
- [ ] Every reviewer finding has a fix or a written reason
- [ ] The PR was approved by someone other than the prompter
- [ ] `git diff m04-done -- backend/app` shows only differences you can explain
