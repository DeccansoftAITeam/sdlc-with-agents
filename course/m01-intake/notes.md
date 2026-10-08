# M1 — Intake and the Constitution (P0)

**Goal:** before any code exists, write down what must never be broken. Agents re-read these files on every task.

> 🎩 **Product Owner + Tech Lead hats** for this whole module.

## 1. Why P0 matters more with agents

A human developer picks up unwritten context over coffee. An agent knows only what is in the repo. Something like "We're multi-tenant" or "AI never replies on its own" has to be **written down**, or the agent will make the wrong call quickly and confidently.

P0 produces three files. Agents treat all three as durable context.

| File | Answers | Template |
|---|---|---|
| `docs/constitution.md` | What are we building, what must always hold, and how good is good enough? | `templates/constitution.md` |
| `docs/architecture/c4-context.md` | Who and what does the system talk to? | C4 level 1 |
| `docs/security/threat-model.md` | What can go wrong, and how will we know it's handled? | `templates/threat-model.md` |

**Gate:** the constitution is approved by both the TL and the PO.

## 2. The constitution in five ideas

1. **Principles tighten, never loosen.** They sit on top of org rules. Example: "Tenant isolation is absolute: enforced by the database, not just code."
2. **Non-goals stop scope creep.** An agent asked to "add notifications" might build an email-ingestion pipeline. A non-goal saying "no email ingestion" stops it.
3. **NFRs need numbers.** "Fast" is not a requirement. "`GET /api/tickets` p95 at 300 ms or less" is, because k6 can check it.
4. **SLOs and error budgets.** An SLO is a target over 28 days. When the budget runs out, feature work stops. You'll wire this up in M11.
5. **The ASVS level decides how much security work you sign up for.** L1 is the baseline. L2 is required when the system handles personal data, authentication or multiple tenants. TicketDesk has all three, so **L2**.

## 3. Threat modelling in four questions

1. What are we working on? (data-flow diagram + trust boundaries)
2. What can go wrong? (STRIDE per element; OWASP LLM Top 10 for AI; LINDDUN for privacy)
3. What will we do about it? (a mitigation per threat)
4. Did we do a good enough job? **Every mitigation names the test or gate that proves it.**

Rule 4 is what makes a threat model more than a document. `TM-003 cross-tenant read` turns into `test_cross_tenant_*` in M4 and an RLS check in M6.

## 4. Where the agent helps (M1 Pair mode)

| Step | Agent does | You do |
|---|---|---|
| Intake | `/grill` interviews you one question at a time, with a recommendation and self-check | Decide |
| Draft review | `/grill` again, on its own draft, hunting contradictions | Decide, then say `apply` |
| Constitution | Fills the template from your answers | Check every number, then approve |
| Threat model | Drafts STRIDE + OWASP rows | Challenge it: what did it miss? |
| C4 | Draws the mermaid diagram | Confirm every arrow |

The agent **drafts**. Humans **decide** and **approve**. An agent-written constitution that nobody challenged is the most expensive file in the repo, because every later task inherits its mistakes.

## 5. TicketDesk decisions from intake

| Question | Decision | Consequence |
|---|---|---|
| Who buys it? | Multi-tenant SaaS | Tenant isolation is threat #1 → ADR-0003 (RLS) in M2 |
| Login? | Own JWT, no SSO | We own auth code → high-risk tier, ADR-0002 in M2 |
| SLAs? | P1: 1 h response … P4: 3 business days | SLA engine → feature TD-007 |
| Sensitivity? | PII in tickets → ASVS L2 | Pen test before launch; masking before LLM |

Then `/grill` on the draft added nine more decisions: self-serve signup, per-tenant identity, `/t/{slug}` routing with the token winning, no attachments, in-app notifications, auth-only email (later dropped entirely: see the 2026-10-08 amendment), AI opt-in, and per-tenant AI caps. See `docs/grill-logs/2026-10-07-constitution.md`. Q6 → Q7 is the one to study: a reasonable answer quietly broke two earlier decisions, and the stress-test step caught it.

## Check yourself

1. Why is "no auto-reply by AI" written as a non-goal and a principle, instead of only in the AI spec?
2. TM-003 is mitigated by "RLS". Which test proves it, and in which gate layer does that test run?
3. A teammate wants to lower the availability SLO from 99.5% to 99% "to ship faster". Which file changes, and who must approve?
