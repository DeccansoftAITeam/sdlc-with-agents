# Glossary

| Term | Meaning |
|---|---|
| **AC** | Acceptance criterion: one testable behaviour, with an ID like `TD-007/AC-3`. Test names contain it |
| **ADR** | Architecture Decision Record: a short document recording a decision that outlives one feature (e.g. "multi-tenancy with RLS") |
| **AGENTS.md** | Plain-language instructions every agent reads at the start of a session |
| **Agent Skills** | Open format for skills (a folder with `SKILL.md`), supported by Claude Code, Copilot and others |
| **ASVS** | OWASP Application Security Verification Standard. L1 is the baseline; L2 applies to apps with personal data, auth or multiple tenants |
| **Audit hook** | Logs every agent tool call to `.agents/audit/audit.jsonl` |
| **Bundle** | Short for the org agent bundle (`agent-bundle` repo) |
| **C4** | A way to draw architecture at levels: context (who talks to the system), containers, components |
| **CODEOWNERS** | GitHub file naming who must approve changes to which paths |
| **Constitution** | `docs/constitution.md`: the project's purpose, principles, non-goals and numeric targets. Every agent reads it |
| **Copier** | The template tool behind `project-scaffold`; `copier copy` generates, `copier update` upgrades |
| **EARS** | Easy Approach to Requirements Syntax: "When <trigger>, the system shall …", "If <bad thing>, then …" |
| **Gate** | A check that blocks progress: a git hook, a CI job, a branch rule. "Instructions guide; gates enforce" |
| **Grill / grilling** | Adversarial Q&A, one question at a time, that finds undecided questions before they become code |
| **Harness** | The program that runs the model and its tools: Claude Code, Copilot Agent mode |
| **Hook** | A script the harness runs on an event; can log or block |
| **M1 / M2 / M3 (modes)** | Agent operating modes: **Pair** (you drive), **Delegated** (one approved task → draft PR), **Unattended** (scheduled CI job). Not to be confused with module numbers |
| **Marketplace** | A git repo that lists Claude Code plugins |
| **MCP** | Model Context Protocol: how agents connect to extra tools (browser, database) |
| **npx** | Runs a Node.js command-line tool without installing it globally |
| **Plugin** | An installable package of skills, subagents and hooks (Claude Code) |
| **PR gate** | CI checks that must pass before a pull request can merge |
| **Problem Details** | Standard JSON error body (RFC 7807): `type`, `title`, `status`, `detail` |
| **RLS** | Row-level security: Postgres filters rows by a policy (here: `tenant_id`), so a query can't see another tenant's data even if the code forgets a filter |
| **Ruleset** | GitHub branch rules (PR required, approvals, required checks) |
| **Scope guard** | Hook that blocks edits outside the active task's approved files |
| **SLA / SLO** | Service Level *Agreement* (what a tenant promises its customers, e.g. reply within 1 h); Service Level *Objective* (our own reliability target, e.g. 99.5% availability) |
| **Squawk** | Linter for SQL migrations that would lock tables or run without timeouts |
| **Subagent** | A separate agent with fresh context and limited tools, used for one job (e.g. review) |
| **tasks.md** | The approved plan: one entry per task with files in scope, budget, skill and done criteria. Agents in M2 may only run approved tasks |
| **Tenant** | One customer company in a multi-tenant system; its data must never mix with another's |
| **uv** | Fast Python package and environment manager |
