<!--
TEMPLATE: Project Constitution  (standard_version 2.0.0)
Location in a project repo: docs/constitution.md
Produced in: P0 Intake & Plan. Amended by PR, never edited silently.
Owners: Tech Lead + Product Owner. Approval: both, recorded at the bottom.
Agents read this file as durable context. Keep it factual and short (target < 250 lines).
Replace every <placeholder>. Delete guidance comments once filled.
-->

# <Project Name> — Constitution

| Field | Value |
|---|---|
| Client | <client name / internal> |
| Project code | <code> |
| Tech Lead | <name> |
| Product Owner | <name> |
| Release Manager | <name> |
| QA Engineer(s) | <names> |
| Standard version | 2.0.0 |
| Last amended | <YYYY-MM-DD> |

## 1. Purpose

<!-- Two or three sentences: who uses this system and what outcome it delivers. -->
<purpose>

## 2. Principles (non-negotiable for this project)

<!-- 5–8 principles. These sit on top of the org rules; they may tighten, never loosen, them. -->
1. <e.g. "Correctness of financial totals over speed of delivery.">
2. <e.g. "Every user-visible AI output carries a citation.">
3. <...>

## 3. Non-goals

<!-- What this project will explicitly NOT do. Prevents scope creep and agent over-reach. -->
- <non-goal>
- <non-goal>

## 4. Stack & deviations

| Layer | Default (04-ARCHITECTURE-DECISIONS.md) | This project | ADR (if deviating) |
|---|---|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 async + Alembic | <same / other> | <ADR-NNNN> |
| Database | PostgreSQL (+ pgvector if RAG) | | |
| Web | Next.js / React | | |
| Mobile | React Native (Expo) | <yes / not in scope> | |
| Cloud target | <provider + service, behind OpenTofu modules> | | |
| LLM provider(s) | via LiteLLM gateway | <models + fallback> | |

## 5. Data sensitivity

| Data category | Examples | Classification (Public / Internal / Confidential / Restricted) | Contains personal data? | Regulated (GDPR, HIPAA, PCI, other)? |
|---|---|---|---|---|
| <category> | <examples> | <class> | <Y/N> | <regime> |

- Data residency: <region(s) where data, logs, backups, embeddings and LLM processing may occur>
- Cross-region / overflow processing allowed? <No / Yes with approval by …>
- Retention: logs <n days>, LLM traces <n days>, backups <n days>, transcripts <n days>

## 6. Non-functional requirements (ISO/IEC 25010:2023)

<!-- Only list characteristics with a concrete target. "N/A" is allowed with a reason. -->

| Characteristic | Requirement | Measured by |
|---|---|---|
| Functional suitability | <e.g. all EARS criteria automated> | Traceability report |
| Performance efficiency | See §7 budgets | k6 release gate |
| Compatibility | <browsers, OS versions, API consumers> | E2E matrix |
| Interaction capability | WCAG 2.2 AA on key flows | axe, no serious/critical |
| Reliability | See §8 SLOs | SLO dashboards |
| Security | ASVS level in §9 | Security gates + review |
| Maintainability | Org gates (coverage 80%, mutation ≥ 60 changed) | PR gate |
| Flexibility | <portability needs, e.g. "must run on any OCI host"> | IaC review |
| Safety | <harm scenarios, esp. AI output> | Threat model + evals |

## 7. Performance budgets

| Flow / endpoint | p95 latency | Error rate | Throughput target | Notes |
|---|---|---|---|---|
| <e.g. GET /api/orders> | <300 ms> | <0.5%> | <50 rps> | |
| Web LCP (key pages) | <2.5 s> | — | — | Lighthouse |
| AI: <feature> end-to-end | <4 s> | <1%> | | includes LLM call |

## 8. Service Level Objectives

<!-- Minimum: availability + p95 latency per user-facing API. AI features add task success + guardrail-trip rate. Window: 28 days unless stated. -->

| SLO | SLI definition | Target | Window |
|---|---|---|---|
| API availability | non-5xx responses / all responses | <99.5%> | 28d |
| API latency | requests < <300 ms> / all | <95%> | 28d |
| AI task success | successful task completions / attempts (eval-labelled sample) | <90%> | 28d |
| AI guardrail-trip rate | requests blocked by guardrails / all AI requests | < <2%> | 28d |

Error-budget policy: when a budget is exhausted, feature work pauses; only reliability fixes ship until the budget recovers (10-OPERATIONS-STANDARD.md).

## 9. Security level

- ASVS level: <L1 (default) / L2 (required if PII, auth, or payments)>
- MASVS profile (mobile): <L1 / L2 / N/A>
- Pen test required before first launch: <Yes if L2 / No>
- Vulnerability disclosure contact (security.txt): <email>

## 10. Recovery objectives

| Objective | Target |
|---|---|
| RPO (max data loss) | <e.g. 15 min> |
| RTO (max downtime to restore) | <e.g. 4 h> |
| Backup method | PITR on managed Postgres + monthly automated restore test |

## 11. Operating model

- Production operator: <Deccansoft / client / shared>
- On-call: <business hours (default) / 24×7 per contract>; hours & timezone: <...>
- Escalation path: <names / roles>
- Hypercare after launch: 30 days by Deccansoft (mandatory if client operates)
- Telemetry backend: <per-client isolated backend name>

## 12. AI use-case summary

<!-- One row per AI feature; full intake lives in each feature spec. Write "None" if no LLM use. -->

| Feature | Purpose | Risk tier | EU AI Act category | Data sensitivity | HITL points | Cost budget / month |
|---|---|---|---|---|---|---|
| <feature> | <purpose> | <Low/Med/High> | <minimal / limited (transparency) / high-risk Annex III / N/A> | <class> | <where a human approves> | <amount> |

## 13. Approval

| Role | Name | Date |
|---|---|---|
| Tech Lead | | |
| Product Owner | | |

## Amendment log

| Date | Change | PR |
|---|---|---|
| <date> | Initial | <#> |
