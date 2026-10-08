# TicketDesk — Constitution

| Field | Value |
|---|---|
| Client | Internal product (multi-tenant SaaS sold to other companies) |
| Project code | TD |
| Tech Lead | DeccansoftAITeam |
| Product Owner | DeccansoftAITeam |
| Release Manager | DeccansoftAITeam |
| QA Engineer(s) | DeccansoftAITeam |
| Standard version | 2.0.0 |
| Last amended | 2026-10-07 |

## 1. Purpose

TicketDesk lets companies (**tenants**) run customer support. Any company can sign up on its own (self-serve); whoever creates the tenant becomes its first admin. The app is **self-contained**: no email and no third-party services, except the AI gateway. Admins bring people in with one-time links they copy and share themselves.

## 2. Principles

1. **Tenant isolation is absolute.** No request, query, cache entry, log line, embedding or LLM prompt may mix data from two tenants. The database enforces it (Postgres row-level security), not just application code.
2. **AI suggests, humans decide.** AI never sends a message to a customer and never closes a ticket. Every AI output is marked as AI-generated and can be edited.
3. **SLA clocks are trustworthy.** SLA timers are computed on the server from stored timestamps and are never derived from client input.
4. **Least data in prompts.** Personal data is masked before any LLM call. Prompts and retrieval run in the tenant's scope only.
5. **Boring auth.** JWT access tokens are short-lived, refresh tokens rotate, and passwords are hashed with Argon2id. No home-grown crypto. **Identity is per tenant:** a user is unique on `(tenant_id, email)`, so the same email in two tenants is two separate users. The JWT carries `tenant_id` and `role`.
6. **Everything observable.** Every request carries `tenant_id` and `trace_id` in telemetry, never PII.
7. **The tenant comes from the token, never the URL.** Tenants are addressed as `/t/{slug}` for routing. After login, `tenant_id` comes only from the JWT; if the slug and the JWT disagree, the request gets 404. Slugs are unique and immutable, and reserved words are blocked.

## 3. Non-goals

- Email, chat or phone channel ingestion. Tickets come from the web app and the API only.
- Billing or subscription management for tenants (set up manually for now).
- Mobile apps.
- SSO / external identity providers (no Entra ID, no OAuth login) in v1.
- Autonomous AI actions: no auto-reply, auto-close, auto-assign or automatic priority changes.
- File attachments (v1).
- **Email of any kind** (notifications, verification, password reset). Notifications are in-app; invites and password resets use one-time links an admin copies and shares.
- **Third-party services other than the AI gateway** (no email provider, no breached-password API, no external identity provider). Keeps the teaching project self-contained.
- Subdomain or custom domain per tenant.

## 4. Stack & deviations

| Layer | Default | This project | ADR |
|---|---|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 async + Alembic | Same | — |
| Database | PostgreSQL (+ pgvector) | Same; Azure Database for PostgreSQL Flexible Server | — |
| Web | Next.js / React | Same | — |
| Mobile | React Native (Expo) | Not in scope | — |
| Cloud target | Cloud-neutral, Azure default | Azure Container Apps, East US 2 | — |
| LLM provider | via LiteLLM gateway | Azure OpenAI (Foundry) `gpt-4.1-mini`, `text-embedding-3-small` via **Azure APIM AI gateway** | ADR-0001 (M2) |
| Auth | — | Self-issued JWT (access 15 min, rotating refresh 7 days) | ADR-0002 (M2) |
| Multi-tenancy | — | Shared DB, `tenant_id` on every row + Postgres RLS; path-slug routing `/t/{slug}` | ADR-0003 (M2) |
| External services | — | **Only** the Azure APIM AI gateway (ADR-0001). Nothing else leaves the system | — |

## 5. Data sensitivity

| Data category | Examples | Classification | Personal data? | Regulated? |
|---|---|---|---|---|
| Tenant account | Company name, slug, AI opt-in flags | Internal | N | — |
| User identity | Name, email, password hash | Confidential | Y | GDPR (EU end-customers possible) |
| Ticket content | Subject, messages, attachments | Confidential | Y (free text may include anything) | GDPR |
| Help articles (KB) | Tenant-authored articles + embeddings | Internal (per tenant) | N | — |
| AI traces | Masked prompts, outputs, scores | Confidential | Masked | GDPR |
| Audit log | Who did what, when | Confidential | Y | — |

- Data residency: Azure East US 2 for the database, logs, backups, embeddings and LLM processing.
- Cross-region processing: **No.** The APIM gateway routes only to East US 2 deployments.
- Retention: logs 30 days, LLM traces 30 days, backups 35 days, closed tickets until the tenant deletes them. Tenant offboarding deletes all rows, embeddings and traces within 30 days.

## 6. Non-functional requirements

| Characteristic | Requirement | Measured by |
|---|---|---|
| Functional suitability | Every EARS criterion has an automated test | Traceability report |
| Performance efficiency | See §7 | k6 release gate |
| Compatibility | Latest 2 versions of Chrome, Edge, Firefox, Safari | Playwright matrix |
| Interaction capability | WCAG 2.2 AA on ticket create, queue and reply | axe: no serious/critical |
| Reliability | See §8 | SLO dashboards |
| Security | ASVS L2 (§9); tenant isolation tests on every endpoint | Security gates + review |
| Maintainability | Coverage ≥ 80%, mutation ≥ 60% on changed code | PR gate |
| Flexibility | Runs on any OCI container host; no Azure SDK in domain code | Architecture lint |
| Safety | No AI output reaches a customer unreviewed | Integration tests + evals |

## 7. Performance budgets

| Flow / endpoint | p95 latency | Error rate | Throughput | Notes |
|---|---|---|---|---|
| `GET /api/tickets` (queue) | 300 ms | < 0.5% | 50 rps | Paginated, max 100 |
| `POST /api/tickets` | 400 ms | < 0.5% | 20 rps | Triage runs async |
| Web LCP (queue, ticket view) | 2.5 s | — | — | Lighthouse |
| AI triage (async, after create) | 5 s | < 2% | — | Ticket is usable before triage finishes |
| AI suggested reply | 6 s | < 2% | — | Includes retrieval |

## 8. Service Level Objectives (28-day window)

| SLO | SLI | Target |
|---|---|---|
| API availability | non-5xx / all responses | 99.5% |
| API latency | requests < 300 ms / all | 95% |
| SLA timer accuracy | escalations fired within 60 s of breach / all breaches | 99.9% |
| AI triage acceptance | triage suggestions not overridden / all triaged tickets (counts only when there are at least 200 triaged tickets in the window) | 80% |
| AI guardrail-trip rate | blocked AI requests / all AI requests | < 2% |

**Product SLA targets (what tenants promise their customers):**

| Priority | First response | Resolution |
|---|---|---|
| P1 Urgent | 1 h | 8 h |
| P2 High | 4 h | 1 business day |
| P3 Normal | 1 business day | 3 business days |
| P4 Low | 3 business days | 10 business days |

SLA clock rules: P1 runs 24×7. P2–P4 run in **tenant business hours** (tenant timezone + weekly schedule; default Mon–Fri 09:00–18:00; no holiday calendar in v1). The resolution clock pauses while a ticket is `pending_customer`. Deadlines are computed from creation minus paused time and are never restarted (TD-007 grill).

Error-budget policy: when a budget is exhausted, feature work pauses until it recovers.

## 9. Security level

- ASVS level: **L2** (personal data, authentication, multi-tenant)
- MASVS: N/A
- Pen test before first launch: **Yes**
- Vulnerability disclosure contact: security@deccansoft.net

## 10. Recovery objectives

| Objective | Target |
|---|---|
| RPO | 15 min |
| RTO | 4 h |
| Backup method | PITR on Postgres Flexible Server + monthly automated restore test |

## 11. Operating model

- Production operator: Deccansoft
- On-call: business hours, IST (09:00–18:00)
- Escalation: On-call developer → Tech Lead → Release Manager
- Telemetry backend: Azure Monitor / Application Insights (one workspace per environment)

## 12. AI use-case summary

| Feature | Purpose | Risk tier | EU AI Act | Data | HITL point | Budget / month |
|---|---|---|---|---|---|---|
| AI triage | Suggest category + priority on new tickets | Medium | Limited (transparency) | Confidential, masked | **Tenant opt-in** (admin, after disclosure); staff can override; override is logged | $20 |
| AI suggested reply | Draft a reply from the tenant's KB (RAG) with citations | Medium | Limited (transparency) | Confidential, masked | **Tenant opt-in**; staff must edit or accept before sending | $40 |

**Per-tenant AI limits (enforced by the APIM gateway):** 200k tokens per calendar month and 20 AI requests per minute. When the cap is reached, AI turns off for that tenant until the 1st of the next month, and the UI says so. The API calls APIM with its managed identity and sets the tenant header on the server side; APIM accepts no other caller.

## 13. Approval

| Role | Name | Date |
|---|---|---|
| Tech Lead | DeccansoftAITeam | 2026-10-07 |
| Product Owner | DeccansoftAITeam | 2026-10-07 |

## Amendment log

| Date | Change | PR |
|---|---|---|
| 2026-10-06 | Initial | M1 |
| 2026-10-08 | **No email, no third-party services except the AI gateway** (PO). Signup is immediate; staff join via admin-copied invite links; resets via admin-issued one-time links; breached-password API replaced by a bundled common-password list | M4 |
| 2026-10-07 | SLA clock rules footnote (TD-007 grill Q1, Q2, Q6) | M2 |
| 2026-10-07 | Grilled (Q1–Q9): self-serve signup, per-tenant identity, slug routing, no attachments, in-app notifications, auth-only email, AI opt-in, per-tenant AI caps | M1 |
