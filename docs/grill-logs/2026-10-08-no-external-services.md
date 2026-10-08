# Decision record — No email, no third-party services (2026-10-08)

| Field | Value |
|---|---|
| Raised by | Product Owner, during M4 (T-001-02 in review) |
| Trigger | "Don't use emails or any other external services. We need a project for demonstrating; students avoid complexities." |
| Decided via | Two targeted questions (not a full grill: the PO's intent was explicit) |

| Q | Decision | Why |
|---|---|---|
| Does "no external services" include AI (Azure OpenAI via APIM)? | **No, AI is the one exception** | AI features (evals, guardrails, kill-switch) are core to a course about agents |
| How do accounts work without email? | **No verification; admin-issued invite and reset links, copied and shared by the admin** | Simplest model that keeps one-time-link security (single use, hashed, expiring) |

## Consequences

| Area | Change |
|---|---|
| Constitution | Non-goals: any email; any third-party service except the AI gateway. ACS row removed |
| C4 | Email provider removed; the AI gateway is the only external system |
| Threat model 2.2 | TM-013 accepts no email verification; TM-014 now covers admin-issued links; TM-015 now covers login only |
| ADR-0002 | HIBP replaced by a bundled common-password list; invite and reset links are admin-issued |
| TD-001 | AC-9, AC-11 removed; AC-1, AC-3, AC-7, AC-10 reworded |
| TD-002 | Invite links shown to the admin; customer registration immediate (rate-limited); new AC-9 (admin-issued reset) |
| Tasks | T-001-02 shrinks to signup + password policy; T-001-04 removed; resets move to T-002-01 |
| Code in review | PR #3 loses the email port, verification endpoints and the HIBP client |
| Schema | `email_tokens.purpose` should become `invite`/`reset` instead of `verify`/`reset`: a T-002-01 migration (expand-contract) |

**Lesson for learners:** requirements change mid-flight. The fix is not to patch code quietly. Amend the constitution, threat model, ADR, specs and tasks first (this PR), so the code change that follows has an approved basis.
