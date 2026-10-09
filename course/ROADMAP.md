# Course roadmap

What the course builds, module by module: skills and agents, pipelines, and security frameworks. ✅ built · 🟡 in progress · ⬜ planned.

The rule throughout: **the course is about the SDLC, not the product.** TicketDesk is kept as small as the lessons allow.

## 1. Modules

| # | Module | Phase | Learners do | Status |
|---|---|---|---|---|
| — | Start here | — | Read: agents, skills, plugins, the scaffold, glossary | ✅ |
| M0 | Setup | — | Toolbox, `doctor.py`, `bootstrap.py`, first prompt in both agents | ✅ |
| M1 | Intake | P0 | `/grill` → constitution, threat model, C4 | ✅ |
| M2 | Specify | P1 | `/spec-draft` → `/grill` → design, ADRs, `tasks.md` | ✅ |
| M3 | Scaffold | P2 | `/scaffold` (Copier), break RLS on purpose, branch ruleset | ✅ |
| M4 | Implement | P3 | **TD-007 only**, from tag `m04-start`: acceptance tests first, scope guard, reviewer subagents, PRs | 🟡 foundations A–D done, TD-007 next |
| M5 | Local gate | P4 | Hook tour; why `--no-verify` is banned; keep pre-push < 90 s | ⬜ |
| M6 | PR gate + review | P5–P7 | Full PR pipeline, preview environment, minimal web slice + E2E smoke | ⬜ |
| M7 | AI feature | P3 (AI) | AI triage (TD-008) through the APIM gateway: evals, guardrails, kill-switch | ⬜ paid Azure |
| M8 | Scheduled | P8 | Nightly deep tests, weekly agent review, unattended agent jobs, conformance | ⬜ |
| M9 | Release gate | P9 | release-please, signed image, SBOM, staging, the 10 checks, PRR | ⬜ paid Azure |
| M10 | Deploy | P10 | Same image → new revision → smoke → swap → rollback drill | ⬜ paid Azure |
| M11 | Operate | P11 | OTel, SLA SLO + burn-rate alert, runbook, game-day incident, postmortem | ⬜ |
| M12 | Capstone | P1→P11 | TD-012 CSAT rating, end to end, alone | ⬜ |

RAG-suggested replies (TD-009) is a **sidebar** in M7, not a module: triage teaches every AI-SDLC point.

## 2. Skills and agents (`agent-bundle`)

| Item | Type | Used in | Status |
|---|---|---|---|
| `grill` | Skill | M1, M2, any design question | ✅ |
| `spec-draft` | Skill | M2, M12 | ✅ |
| `scaffold` | Skill | M3, scaffold upgrades | ✅ |
| `acceptance-tdd` | Skill | M4, M7, M12 | ✅ |
| `migration-writer` | Skill | M4 | ✅ |
| `test-generator` | Skill | M8 | ✅ |
| `code-reviewer` | Subagent (read-only) | Every PR | ✅ |
| `security-reviewer` | Subagent (read-only) | High-risk PRs; weekly in M8 | ✅ |
| Audit-log hook | Hook | Always | ✅ |
| Scope-guard hook | Hook | M2-mode tasks | ✅ |
| `eval-runner` | Skill | M7 | ⬜ bundle v2.2 |
| `ai-redteam` | Subagent | M7 | ⬜ bundle v2.2 |
| `release-captain` | Skill | M9 | ⬜ bundle v2.3 |
| `incident-commander` | Skill | M11 | ⬜ bundle v2.4 |

Kun tools: `treehouse` (M4 sidebar), `no-mistakes` (M5, optional), `gnhf` (M8), `backpass` (M11). `/kun` itself stays rejected (unpinned remote code).

## 3. Pipelines

| Workflow | Module | Jobs | Status |
|---|---|---|---|
| Local gate (pre-commit / pre-push) | M3, M5 | gitleaks, ruff, mypy, pytest + 80% coverage, architecture tests, squawk, Nx affected | ✅ |
| `pr-gate.yml` v1 | M3 | hygiene, backend, web | ✅ |
| `pr-gate.yml` v2 | M6 | + contract tests (Schemathesis), breaking-change check (oasdiff), migration safety, AC traceability, mutation on changed code, SAST (semgrep), dependency/CVE gate, agent attribution, E2E smoke | ⬜ |
| `preview.yml` | M6 | Per-PR environment (one shared Container Apps environment, scale to zero) | ⬜ |
| `conformance.yml` | M8 | Bundle/scaffold drift, required files, RLS everywhere | ⬜ |
| `nightly.yml` | M8 | Full mutation, fuzzing, full E2E, DAST (ZAP), load (k6), full AI evals, Trivy | ⬜ |
| `weekly-review.yml` | M8 | `security-reviewer` on `main`, stale flags, drift report | ⬜ |
| `agent-unattended.yml` | M8 | M3-mode jobs (dependency bumps, `gnhf`), report-only first | ⬜ |
| `release.yml` | M9–M10 | release-please, build once, cosign, SBOM, staging, sign-offs, revision swap, rollback | ⬜ |

Each pipeline ships as a `project-scaffold` release (v1.1–v1.4) pulled in with `copier update`.

## 4. Security frameworks

| Framework | Where | Status |
|---|---|---|
| STRIDE threat model (TM-001…016) | M1, deltas per feature | ✅ |
| OWASP ASVS L2 | Constitution target, auth reviews | ✅ partial (MFA is an accepted gap) |
| OWASP Top 10 for LLM apps (2025) | Modelled in M1, tested in M7 | 🟡 |
| OWASP Agentic Top 10 | Our coding-agent setup: permissions, scope guard, audit, allow-list | ✅ |
| LINDDUN (privacy) | Threat model | ✅ |
| Tenant isolation (forced RLS) | Every table, architecture test, cross-tenant test per endpoint | ✅ |
| Secret scanning (gitleaks) | Commit hook + CI | ✅ |
| SAST (semgrep + ruff security rules) | PR gate | 🟡 ruff only |
| Dependency / CVE SLAs | PR gate + nightly | ⬜ M6/M8 |
| DAST (ZAP), API fuzzing (Schemathesis) | Nightly / PR | ⬜ M6/M8 |
| Supply chain: SBOM, signed images, pinned actions | Release gate | ⬜ M9 |
| OWASP SAMM | M11 sidebar | ⬜ |
| EU AI Act Art. 4 (AI literacy) / transparency | Completion record; AI labels in M7 | ⬜ |

## 5. Azure costs (asked before creating)

| Module | Resource | Rough cost |
|---|---|---|
| M7 | APIM Consumption + Azure OpenAI | Pay per call; cents per day while learning |
| M6 | Preview environments | Shared Container Apps environment, scale to zero |
| M9–M10 | Container Apps, Postgres Flexible B1ms, ACR Basic, Key Vault | About $25–40/month while running |
