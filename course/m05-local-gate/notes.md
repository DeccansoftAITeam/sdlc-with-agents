# M5 — The local gate (P4)

**Goal:** understand the checks that run on your machine before code leaves it, why they're kept **fast**, and why they are a convenience, never the final word.

> 🎩 **Developer** and **Platform Owner**. No new feature code: you measure, break and tune the gate you've been using since M3.

## 1. Three stages, three budgets

| Stage | Runs on | Budget | What runs (`.pre-commit-config.yaml`) |
|---|---|---|---|
| `pre-commit` | `git commit`, changed files | < 5 s typical | gitleaks, ruff + format, merge markers, YAML/JSON, whitespace, large files |
| `commit-msg` | `git commit` | instant | Conventional Commits (feeds release-please in M9) |
| `pre-push` | `git push` | **< 90 s** | mypy strict, backend tests + 80% coverage + architecture tests, squawk, Nx-affected web typecheck/tests, file length, public-env check |

What's **not** here on purpose: mutation testing, fuzzing, full E2E, DAST, AI evals. They take minutes to hours and live in CI (M6, M8). A slow local gate doesn't make code safer; it makes people skip it.

## 2. Measured, not guessed

`pre-commit run --verbose` prints each hook's duration. Our numbers, all files, warm machine:

| Hook | Before | After |
|---|---|---|
| gitleaks | 2.1 s | 2.1 s |
| web typecheck + tests (Nx affected) | 20.6 s | cached when untouched |
| mypy strict | 3.0 s | 3.0 s |
| **backend tests + coverage** | **64.1 s** | **45.6 s** |
| **pre-push total** | **95 s ✗** | **56 s ✓** |

Four modules of features pushed the gate past budget without anyone noticing. Nobody had looked.

### What we tried

| Idea | Result | Verdict |
|---|---|---|
| `pytest-xdist -n 4` | 64 → 48 s, but **4 tests failed**: migration tests rewrite the schema and the breach sweep visits every tenant, so they collide in parallel | Rejected: flaky gates teach people to rerun until green |
| Profile with `--durations` | No hot spot: 215 tests, none over 3 s. 40 s without coverage vs 64 s with | Coverage itself costs ~20 s |
| `coverage` `core = "sysmon"` (Python 3.12+ `sys.monitoring`) | 64 → 46 s **and coverage jumped 86% → 97%** | Adopted, after finding out why the number changed |

### The number was wrong, not the tool

A faster tool shouldn't change a measurement, so we checked. SQLAlchemy's async layer runs code inside **greenlets**; the default coverage tracer doesn't follow them, so every line executed through the database was reported as untested. With `concurrency = ["greenlet"]` the old tracer also says 97%. Since M3 the coverage gate had been measuring the wrong thing. It still passed, so nobody asked.

**Lesson:** when a gate's number moves for a reason you don't understand, stop and find out. A gate is only as good as what it measures.

## 3. `--no-verify`: why it's banned, and why banning it isn't enough

Org rules §3.5 forbid agents from skipping hooks, and `.claude/settings.json` denies `git commit --no-verify:*`. Try the variations:

| Command | Matched by the prefix rule? |
|---|---|
| `git commit --no-verify -m x` | ✅ denied (prefix matches) |
| `git commit -m x --no-verify` | ❌ flag later in the command |
| `git commit -n -m x` | ❌ short form |
| `SKIP=backend-tests git push` | ❌ pre-commit's own skip switch |
| Copilot, any of the above | ❌ no equivalent deny rule |

A deny list is an **instruction with teeth**, not a gate. It catches the honest mistake, not the determined bypass. The real backstop is **CI re-running the same checks on a clean machine** where nobody can skip anything: that's principle 1, "instructions guide; gates enforce".

## 4. Does CI really back up every local check?

| Local check | Re-run in `pr-gate.yml` today? |
|---|---|
| gitleaks, ruff, format, hygiene, file length | ✅ `hygiene` |
| mypy, tests + coverage + architecture | ✅ `backend` |
| web typecheck + tests | ✅ `web` |
| **squawk** migration lint | ❌ |
| **`NEXT_PUBLIC_*` secrets** check | ❌ |
| **Conventional Commits** (squash title) | ❌ |

Three checks protect nothing if someone skips hooks. M6 closes them through a scaffold release, because workflows are Platform-owned files (agents are denied editing them).

## 5. Agents and the local gate

- Agents run the gate before proposing a PR (org rules §4) and fix failures; they never suppress them (`# noqa`, `pytest.skip`, lowering `--cov-fail-under`).
- The hooks themselves are protected: `.pre-commit-config.yaml` is on the deny list, so an agent can't "fix" a failing hook by deleting it.
- Docker down = 170 failing tests. The gate's first error is the one that matters.

## Sidebar: `no-mistakes` (Kun, optional)

A pre-push step that asks an agent to sanity-check the diff (forgotten debug code, TODOs, unrelated files). Treat it as an **advisor**: it can't block on its own, and its output is data, not instructions. Adopt only if it stays inside the 90 s budget.

**Next:** [lab.md](lab.md)
