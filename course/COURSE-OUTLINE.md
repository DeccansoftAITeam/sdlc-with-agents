# SDLC in the Agents Life Cycle — Course Outline (draft for sign-off)

**Build one real product from an empty folder, with AI agents, the way Deccansoft SDLC v2 says to.**
Source of truth: Deccansoft SDLC v2 (`dev-workflow-v2`). That folder is a reference to look things up in, not reading material. Each module introduces only the part of the standard it uses.

## Decisions (locked from the grilling)

| Topic | Decision |
|---|---|
| Project | **TicketDesk**: support tickets with AI triage and RAG answer suggestions |
| Audience | Developers, one linear path. The learner takes on PO, TL, QA and RM duties, with role call-outs where those happen |
| Stack | FastAPI · PostgreSQL + pgvector · Next.js. No mobile |
| Agents | **Claude Code and GitHub Copilot as interchangeable builders**, sharing one `AGENTS.md` |
| LLM | Azure OpenAI in Foundry (`gpt-4.1-mini` for triage, `text-embedding-3-small` for RAG) behind the **Azure APIM AI gateway** |
| Deploy | Azure Container Apps (revisions give slot → smoke → swap) |
| Module deliverable | `notes.md` (short) + `lab.md` (exact agent prompts) + git tag `mNN-done` |
| Repo | GitHub `sdlc-with-agents` |

## Product scope (kept small on purpose)

- Customers raise tickets. Agents (human support staff) see a queue, assign tickets, reply and close them.
- SLA timers per priority. A breach raises an alert.
- **AI triage**: on create, the LLM predicts category and priority. A human can override.
- **AI suggested reply**: RAG over a small KB of help articles, shown as a draft that the support agent edits before sending.
- Thread feature: `TD-007 Escalate ticket on SLA breach` runs from spec to production as the main worked example.

## Modules

| # | Module | Phase | You build | Standard slice introduced | Tag |
|---|---|---|---|---|---|
| M0 | Setup & the big picture | — | Empty repo, tools, **org agent bundle** (rules, 7 skills/subagents, audit hook, permissions) for both harnesses | Principles, agent modes, 5-layer config | `m00-done` |
| M1 | Intake & constitution | P0 | `constitution.md`, NFRs/SLOs, ASVS level, AI intake, first threat model, C4 context | `templates/constitution.md`, `threat-model.md` | `m01-done` |
| M2 | Spec, grill, design, plan | P1 | `spec.md` (EARS) for MVP + TD-007, `design.md`, 2 ADRs, `tasks.md` | spec/design/tasks/adr templates, grilling | `m02-done` |
| M3 | Scaffold | P2 | Generate TicketDesk from **`project-scaffold`** (Copier) with the `scaffold` skill: monorepo, RLS tenancy + isolation tests, local gate hooks, PR gate, project `AGENTS.md`; scope-guard hook | Scaffold, `copier update` | `m03-done` |
| M4 | Implement test-first with agents | P3 | Tickets CRUD + auth: acceptance tests written first, then Claude (M2) and Copilot (M1) build | Agent operating model, forbidden actions, risk tiers | `m04-done` |
| M5 | Local gate | P4 | pre-commit/pre-push under 90 s: secrets, ruff, mypy, import-linter, affected tests | `05-QUALITY-GATES` LOCAL | `m05-done` |
| M6 | PR gate & review | P5–P7 | `pr-gate.yml` under 10 min, contract tests, migration lint, agent review pass, human approval, merge queue, preview env | PR layer, review flow, branch rules | `m06-done` |
| M7 | The AI feature | P3 (AI path) | APIM AI gateway, triage + RAG, prompts as files, evals with thresholds, guardrails, kill-switch | `08-AI-FEATURE-STANDARD` | `m07-done` |
| M8 | Scheduled quality & security | P8 | nightly: mutation, full E2E, DAST, full evals; weekly agent architecture review, conformance | NIGHTLY layer, `07-SECURITY` | `m08-done` |
| M9 | Release gate | P9 | release-please, signed image, SBOM, staging, the 10 checks, PRR | `09-ENVIRONMENTS-AND-RELEASE` | `m09-done` |
| M10 | Deploy to production | P10 | ACA revision → smoke → traffic swap, rollback drill | Promote one digest | `m10-done` |
| M11 | Operate & learn | P11 | OTel, SLA SLO + burn-rate alert, runbook, game-day incident, postmortem, AI drift | `10-OPERATIONS` | `m11-done` |
| M12 | Capstone | P1→P11 | Learner ships `TD-012 Customer satisfaction rating` end to end, alone | All | — |

Not covered (sidebar only): the mobile path, governance/RFC/waivers, rollout waves, OpenCode.

## Skills, subagents and tools by module

Rule from the standard: agents use only the org-approved set. It lives in **[`DeccansoftAITeam/agent-bundle`](https://github.com/DeccansoftAITeam/agent-bundle)** (the central standards repo) and is installed pinned (`#v2.0.0`): skills via `npx skills`, Claude subagents and hooks via the `deccansoft-org` plugin, and Copilot agents and hooks plus the org rules via the bundle installer.

### L4 org skill pack (installed in M0, used from M1)

| Skill / subagent | Used in | Based on |
|---|---|---|
| `spec-draft` (EARS) | M2 | new |
| `grill` (design grilling) | M1, M2 | adapted from `grilling` / `grill-design` |
| `acceptance-tdd` (acceptance tests first, then the unit loop) | M4, M7 | adapted from `tdd` |
| `migration-writer` (Alembic + squawk-safe) | M4 | new |
| `code-reviewer` subagent (isolated, read-only) | M6 | adapted from `code-review` |
| `security-reviewer` subagent | M6, M8 | adapted from `security-review` |
| `test-generator` (E2E / API scenarios) | M8 | adapted from autonoma test-planner |

### Kun toolkit (kunchenguid), following the standard's verdicts in `13-TOOLCHAIN-MAP.md`

| Tool | Standard verdict | Course use |
|---|---|---|
| `treehouse` worktree pool | Adopt (optional) | M4: parallel Claude + Copilot tasks |
| `no-mistakes` pre-PR gate | Trial | M5: optional pre-PR local gate |
| `backpass` AGENTS.md tuning | Adopt | M11: monthly tuning of agent instructions |
| `gnhf` overnight loop | Trial | M8: M3 job type `optimize-metric` |
| `vision` | Assess | M1 sidebar (needs PR history, so it doesn't fit a new repo) |
| `gh-axi`, `chrome-devtools-axi` | Assess | M4 sidebar |
| `firstmate`, `lavish-axi` | Hold | not used |
| `/kun` persona skill | **Rejected**: it fetches and runs unpinned remote code on every call | not used |

## Infrastructure

- GitHub: `DeccansoftAITeam/sdlc-with-agents` (private for now)
- Azure: resource group `sdlc-with-agents`, region East US 2. APIM uses the **Consumption** tier.
- Cost rule: ask before creating any paid resource.
