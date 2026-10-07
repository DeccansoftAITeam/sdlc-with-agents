# Grill log — Constitution v1 (P0)

| Field | Value |
|---|---|
| Skill | `grill` (org skill, standard 2.0.0) |
| Subject | `docs/constitution.md` v1 + `docs/security/threat-model.md` v1 |
| Interviewer | Claude Code (Opus 5.5), M1 Pair |
| Decider | Product Owner / Tech Lead |
| Date | 2026-10-07 |
| Outcome | 9 decisions, 3 new threats, 1 threat withdrawn, 1 self-caught conflict |

| Q | Area | Question | Recommendation | Self-check raised | Decision | Stress-test after the answer |
|---|---|---|---|---|---|---|
| 1 | Tenancy | How does a company become a tenant? | Self-serve | Public signup = abuse and cost surface | **Self-serve** | Billing is a non-goal → free tenants → per-tenant AI quota + signup rate limit (TM-013) |
| 2 | Identity | How do customers get access? | Registered accounts | Same email across tenants → linking risk | **Registered** | Identity is per tenant: `UNIQUE(tenant_id, email)`; login needs tenant context |
| 3 | Routing | How does a request find its tenant before login? | Path slug `/t/{slug}` | Code may trust the slug over the JWT | **Slug** | Mismatch → 404 + architecture test; immutable slugs, reserved words |
| 4 | Scope | Attachments in v1? | Out | Learners may find it unrealistic | **Out** | TM-010 withdrawn; no Blob Storage |
| 5 | TD-007 | Behaviour on SLA breach? | Flag + notify, no priority change | Email adds a provider + PII flow | **Flag + notify** | Channel left open → Q6 |
| 6 | Integrations | Notification channel? | In-app only | A 2 a.m. breach goes unseen | **In-app only** | ⚠ **Conflicts with Q1/Q2**: verification and reset still need email → Q7 |
| 7 | Identity | How are verify/reset messages sent? | ACS Email, auth only | Adds a dependency + 2 threats | **Auth-only email** | TM-014 token handling, TM-015 enumeration |
| 8 | AI | AI on by default? | Opt-in per tenant | Small sample makes the AI SLO noisy | **Opt-in** | SLO counts only at ≥ 200 triages; demo tenant seeded with AI on |
| 9 | Cost | Per-tenant AI limit? | 200k tokens/month + 20 req/min | Tenant header must be server-set | **Hard cap** | APIM accepts only the API's managed identity (LLM10) |

**Lesson for learners:** Q6 → Q7. A sensible answer to one question (no email) silently broke two earlier ones (verification and reset). The stress-test step after each answer caught it. Without that step, the conflict would have surfaced in M4 as a failing signup test, or not at all.
