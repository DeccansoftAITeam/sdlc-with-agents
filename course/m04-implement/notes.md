# M4 — Implement test-first with agents (P3)

**Goal:** turn an approved `tasks.md` into merged code by delegating to agents **inside guardrails**: acceptance tests first, scope enforced, reviewed by agents and then by humans.

> 🎩 **Developer** prompts; agents work in **M2 Delegated** mode, one task at a time; a different human approves. You build **TD-007** (SLA breach escalation) from tag `m04-start`.

## 1. What already exists at `m04-start`

The foundations were built with exactly the workflow you're about to use, in five PRs (A–E in `docs/specs/FOUNDATIONS-tasks.md`). You start with:

| Spec | You get |
|---|---|
| TD-001/002 | Signup, login (EdDSA JWT + rotating refresh), roles, admin-created accounts, append-only audit log |
| TD-003/004 | Tickets, queue with cursor pagination, replies, internal notes, status machine |
| TD-005 | `compute_deadlines()` (pure, DST-safe), SLA policy per tenant, deadlines stored on every ticket |
| TD-006 | `notify()` with dedupe keys, inbox API, 90-day retention |

TD-007 only has to **detect** breaches and **escalate** them. Everything it depends on is tested.

## 2. The operating model in one picture

```
tasks.md (approved)          ← the plan IS the permission (M2)
   │  /acceptance-tdd T-007-02
   ▼
Phase 0  write .agents/progress/T-007-02.md, set ACTIVE   → scope_guard hook now blocks other files
Phase A  acceptance tests from the EARS criteria, RED for the right reason
   ⏸  STOP: a human reviews the tests (they are the contract)
Phase B  red → green in vertical slices; unit tests as needed
Phase C  local gate · code-reviewer (+ security-reviewer if High) · fix or answer every finding
   ▼
draft PR on agent/T-007-02-…  → CI → human code-owner review (not the prompter) → squash merge
```

Four things make this safe, and only one of them is an instruction:

| Control | Kind | Where |
|---|---|---|
| "Only touch Files in scope" | Instruction | `tasks.md`, org rules §4 |
| `scope_guard.py` blocks out-of-scope edits | **Gate** | PreToolUse hook (Claude + Copilot) |
| Reviewer subagents are read-only | **Gate** | Their tool list has no Edit/Write/Bash |
| Prompter can't approve; checks required | **Gate** | GitHub ruleset on `main` (M3) |

## 3. Acceptance tests are the contract

- Names carry the AC id: `test_td007_ac7_repeated_and_concurrent_sweeps_notify_once`.
- They run against the **real database as the runtime role**, so RLS is real in tests.
- No fake clock: TD-007 tests move a stored deadline into the past and run one sweep. The code uses the DB's `now()` only (constitution: "SLA clocks are server-side").
- **Prove they bite.** Tests written after code can pass vacuously. Break the code on purpose (drop the `IS NULL` guard; ignore the flag) and watch them go red. We did; both did.

## 4. Risk tiers decide the review

| Tier | Example in TD-007 | Reviews |
|---|---|---|
| **High** | T-007-01 migration (new SECURITY DEFINER function, RLS policy) | `code-reviewer` + `security-reviewer`, 2 human approvals incl. Tech Lead |
| Medium | T-007-02 sweep, T-007-03 queue | `code-reviewer`, 1 human approval |
| Low | T-007-05 metrics | Human review |

## 5. What actually went wrong while building the foundations

Every one of these was caught by a test, a gate or a reviewer, never by luck. Expect the same classes in your build.

| Caught by | What happened |
|---|---|
| Architecture test | Alembic autogenerate **never** emits RLS. Four migrations, four times added by hand (`migration-writer` step 4) |
| Acceptance test | `-> TicketOut` on a handler silently became the response model and dropped `messages` |
| squawk (pre-push) | 32-bit ticket number vs 64-bit counter; concurrent index not rerunnable (`IF NOT EXISTS`) |
| Hypothesis | Windows has no IANA timezone database: added `tzdata` |
| code-reviewer | A valid SLA policy (1 h a week, 60-day target) turned every new ticket into a 500 |
| code-reviewer | Tickets resolved before the TD-007 deploy would breach the moment they were reopened |
| security-reviewer | One failing tenant would stall the sweep for every tenant after it |
| Gate run | Docker stopped: 172 "failures" that were one missing database. Read the first error |

## 6. Scope amendments are normal; silent scope creep isn't

Every PR needed a file the plan didn't list (`users/deps.py`, `tzdata`, a feature folder for flags). Each time: stop, ask, and record a row in the **Scope amendments** table with the reason and the approver. The reviewer reads that table; an unexplained file in the diff is a finding.

## 7. Claude Code and Copilot are interchangeable here

Same skills (`npx skills` install), same hooks (`.github/hooks/` for Copilot), same `AGENTS.md`. `tasks.md` marks T-007-02 and T-007-03 as parallel: one agent each, each in its own worktree (`treehouse` sidebar). The lab runs them one after another to stay simple.

## Sidebar: `treehouse`

A pool of git worktrees so two agents never share a working copy. Adopt it when you genuinely run lanes in parallel; skip it otherwise. It changes nothing about the gates.

**Next:** [lab.md](lab.md)
