# M3 — Scaffold (P2)

**Goal:** generate a repo where every practice already works on day one, so the first line of agent code lands inside the guardrails.

> 🎩 **Tech Lead** drives; the agent runs the `scaffold` skill in **M1 Pair** mode, because the scaffold writes gate configs.

## 1. Why a scaffold, not "set up the repo"

Standard principle 2: **nothing is adopted per project**. If each team wires up hooks, CI, RLS and agent config by hand, every repo ends up different and some end up without them. The scaffold is a **versioned template repository**:

```
DeccansoftAITeam/project-scaffold  (Copier template, tagged v1.0.x)
        │  copier copy   (new project)
        │  copier update (pull later scaffold releases into existing projects)
        ▼
your repo  +  .copier-answers.yml  (which scaffold version, which answers)
```

Three org repos now work together:

| Repo | Holds | Changed by |
|---|---|---|
| `agent-bundle` | How **agents** behave: rules, skills, subagents, hooks | Platform Owner |
| `project-scaffold` | How a **repo** starts: layout, gates, guardrails, templates | Platform Owner |
| your project | What **your product** is: constitution, specs, code | Your team |

## 2. What you get on day one

| Layer | In the generated repo | Proves itself by |
|---|---|---|
| Tenancy | `tenant_session()`, `TenantOwned`, `enable_rls()`, separate owner and runtime DB roles | 5 RLS tests: no cross-tenant read or write, fails closed without a tenant, can't switch RLS off |
| Architecture | Routers without SQL, no cloud SDK in domain code, every `tenant_id` table has forced RLS | `tests/architecture/` |
| LOCAL gate | pre-commit (secrets, lint, format, hygiene, conventional commits) + pre-push (mypy, tests + 80% coverage, Nx affected, squawk, file length) | Auto-installed; about 45–55 s warm |
| PR gate | `pr-gate.yml` (v1 subset) | Runs on the first PR in M6 |
| Agent guardrails | Permission files, CODEOWNERS, bundle pinned at `v2.1.2` | M0 checks, scope guard in M4 |

## 3. The scaffold caught real problems before any feature code existed

Generating TicketDesk surfaced four defects, all found by gates rather than reviewers:

| Found by | Problem | Fixed in |
|---|---|---|
| `end-of-file-fixer` | Bundle hook JSON had no final newline | agent-bundle v2.1.1 |
| `ruff-format` | Template whitespace didn't match the formatter | scaffold v1.0.0 |
| **squawk** | Migrations had **no `lock_timeout`/`statement_timeout`**, so a migration could stall production behind a lock | scaffold v1.0.1 |
| `copier update` | Post-generation tasks broke updates | scaffold v1.0.2 + `scaffold` skill v2.1.2 |

The squawk finding is the one to remember: on a busy table, a migration with no lock timeout queues behind traffic, and every request behind it waits. A gate found it before anyone wrote a table.

## 4. The scope guard: "stay in scope" becomes a gate

`tasks.md` says which files a task may touch. The `scope_guard` hook (bundle v2.1+) enforces it **while the agent works**:

```
.agents/progress/ACTIVE           → T-007-02
.agents/progress/T-007-02.md      → ## Files in scope
                                     - `backend/app/features/sla/sweep.py`
agent edits backend/app/features/auth/login.py  →  BLOCKED: outside Files in scope of T-007-02
```

No `ACTIVE` file means no task, which means M1 pair work: nothing is blocked. You'll see the guard fire in M4.

## 5. Three kinds of hooks (don't mix them up)

| Kind | Example | Comes from | Taught in |
|---|---|---|---|
| Agent hooks | audit log, scope guard | agent-bundle | M0, M4 |
| Git hooks | pre-commit / pre-push | project-scaffold | **M5** |
| CI workflows | pr-gate, nightly, release | project-scaffold | M6, M8, M9 |

## Check yourself

1. A teammate wants to "just add" a pre-commit hook to TicketDesk directly. What's wrong with that, and where should the change go?
2. Why does the scaffold create **two** database roles?
3. `copier update` brings a new workflow file that conflicts with a local edit. Which version wins, and why?
