# 5. The project scaffold

Repo: [`DeccansoftAITeam/project-scaffold`](https://github.com/DeccansoftAITeam/project-scaffold). It's the **template every new project is generated from**, so every practice in the standard is in place on day one, before any agent writes a line.

## Why a template, and why this kind

| Without a template | With `project-scaffold` |
|---|---|
| Each team wires up hooks, CI, auth patterns and agent config by hand; every repo ends up different, and some end up with none | Every project starts identical and already gated |
| "We'll add tests and security checks later" (later never comes) | Gates are on from the first commit; agents' very first code is checked |
| Fixes to the shared setup never reach old projects | **`copier update`** pulls a new template release into an existing project, as a reviewable diff |

It's built with **[Copier](https://copier.readthedocs.io)**, a project-template tool. You answer a few questions (name, ASVS level, multi-tenant?, AI features?), it renders the files, and it records your answers and the template version in **`.copier-answers.yml`**. That file is what makes later updates possible: Copier knows what you started from.

## What's inside, and why each tool is there

### Backend (`backend/`)

| Tool | What it is | Why we use it |
|---|---|---|
| **Python 3.12+** + **uv** | Language + a very fast package/venv manager | `uv.lock` pins every dependency; installs in seconds in CI |
| **FastAPI** | Async web framework | Typed request/response models; OpenAPI generated for free |
| **SQLAlchemy 2.0 (async)** + **asyncpg** | Database toolkit + Postgres driver | Mature, typed queries; no hand-built SQL strings |
| **Alembic** | Database migrations | Versioned schema changes, run as a separate owner role |
| **pydantic-settings** | Config from environment variables | No environment-specific code branches (12-factor) |
| **OpenTelemetry** | Traces and metrics | Same observability in every project (M11) |
| **Problem Details** errors | Standard JSON error format (RFC 7807) | Consistent errors; never leaks stack traces |

### Database (`db/`, `docker-compose.yml`)

| Piece | Why |
|---|---|
| **PostgreSQL 17 + pgvector** in Docker | One command (`docker compose up -d db`) gives every developer the same database, including vector search for the AI features |
| **Two database roles** | An *owner* role runs migrations; the app runs as a role that **can't bypass row-level security** |
| **Row-level security (RLS) helpers** | `tenant_session()`, `TenantOwned`, `enable_rls()`. Tenant isolation is enforced by the database, not just by code |

### Frontend (`apps/web`, `packages/core`)

| Tool | Why |
|---|---|
| **Next.js + TypeScript** | Mainstream React framework; `/api` proxied to the backend (no CORS, cookies stay first-party) |
| **pnpm** workspaces + **Nx** | One repo for backend, web and shared packages; Nx runs only what a change *affects* |
| **Vitest** | Fast unit tests |
| `packages/core` | Shared types and the **generated** API client (never hand-edited) |

### Tests that ship with the template

| Test | Proves |
|---|---|
| RLS isolation tests | The app role can't read or write another tenant's rows, and can't switch RLS off |
| Architecture tests | Routers don't touch the database; no cloud SDK in domain code; every table with `tenant_id` has forced RLS; no file over 1000 lines |
| Health and error tests | `/healthz`, `/readyz`, Problem Details |

You'll break one of these on purpose in M3 and watch it catch a cross-tenant data leak.

### The local gate (git hooks, `.pre-commit-config.yaml`)

Installed automatically. **pre-commit** is a framework that runs checks when you commit or push.

| When | Checks | Tool |
|---|---|---|
| On commit (fast) | Secrets never reach history | **gitleaks** |
| | Lint and format Python | **ruff** |
| | Merge markers, YAML/JSON, file size, whitespace | pre-commit hooks |
| | Commit messages follow Conventional Commits | conventional-pre-commit |
| On push (< 90 s) | Strict type checking | **mypy** |
| | Tests + 80% coverage + architecture tests | **pytest** |
| | Web typecheck + tests, affected only | **Nx** |
| | Migration safety (no table-locking DDL, timeouts set) | **squawk** |
| | File length, no secrets in public env vars | small scripts |

Agents run the same hooks, and they're forbidden from using `--no-verify`.

### CI and guardrails

| File | Purpose |
|---|---|
| `.github/workflows/pr-gate.yml` | The same checks on a clean machine for every PR (grows in M6, M8, M9) |
| `.claude/settings.json` | Claude permissions (allow / ask / deny) + the pinned bundle plugin |
| `.vscode/settings.json` | Copilot terminal guardrails |
| `CODEOWNERS` | Who must approve changes to gates, agent config and high-risk code |
| `AGENTS.md` skeleton, `docs/templates/` | Where project facts go; templates for every SDLC document |

### And after generation

A post-generation step installs the **agent bundle** at a pinned version (page 3), so the project is agent-ready immediately.

## How it was proven

The scaffold isn't a theory. Generating TicketDesk from it surfaced real defects, all caught by its own gates and fixed in released versions: **squawk** found migrations without lock timeouts (v1.0.1), `copier update` exposed broken post-generation tasks (v1.0.2), and a learner hit a wrong permission rule (v1.0.4). That's the point of a versioned template: fix it once, and every project gets the fix through `copier update`.

Next: [6. How the three repos fit together](06-three-repos.md)
