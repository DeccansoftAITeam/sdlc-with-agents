# TD-008: AI triage suggests category and priority

| Field | Value |
|---|---|
| Status | **Draft**: for PO and TL review |
| Product Owner | DeccansoftAITeam |
| Tech Lead | DeccansoftAITeam |
| Change-risk tier | **High** (AI; ticket content leaves the system, masked) |
| Feature flag | `ai-triage` (per tenant, default off; owner: TL; removal: never, it's the opt-in) |
| Related ADRs | ADR-0004 (AI gateway), ADR-0003 (multi-tenancy) |
| Depends on | TD-003 (tickets), TD-005 (priority drives SLA deadlines) |

## 1. Problem & outcome

Staff set category and priority by hand on every new ticket. It's slow, and priority is often left at the default, so SLA deadlines are wrong from the start.

Success measure: **AI triage acceptance ≥ 70%** (suggestions accepted without change, constitution §9) and median time-to-triage down 50% for opted-in tenants.

## 2. User stories

- **US-1** As **support staff**, I want a suggested category and priority on each new ticket, with a short reason, so that I can triage with one click.
- **US-2** As **support staff**, I want to accept, change or ignore the suggestion, so that I stay in control.
- **US-3** As a **tenant admin**, I want to turn AI triage on or off for my tenant after reading what it sends, so that we decide whether our customers' text goes to an AI provider.
- **US-4** As a **tenant admin**, I want AI to stop for the month when our budget is used, and to be told, so that costs stay predictable.

## 3. Acceptance criteria (EARS)

| ID | Story | Criterion (EARS) | Test layer |
|---|---|---|---|
| TD-008/AC-1 | US-1 | When a ticket is created in a tenant with `ai-triage` on, the system shall store a suggestion (category, priority, reason ≤ 200 chars) within 5 s at p95, without delaying ticket creation. | integration + eval |
| TD-008/AC-2 | US-2 | The system shall never change a ticket's category or priority from a suggestion without a staff action. | integration |
| TD-008/AC-3 | US-2 | When staff accept a suggestion, the system shall apply it through the normal ticket update (so SLA deadlines recompute, TD-007/AC-13) and record "accepted"; when staff set different values, the system shall record "overridden". | integration |
| TD-008/AC-4 | — | The system shall send the model only the ticket subject and body, with emails, phone numbers and card-like numbers masked, and never names, account data or other tickets. | unit + log capture |
| TD-008/AC-5 | — | The system shall accept model output only if it matches the schema (category in the fixed list, priority P1–P4); otherwise it shall store no suggestion and count a guardrail trip. | unit |
| TD-008/AC-6 | US-4 | While a tenant has used its monthly AI tokens (200k) or 20 requests in the current minute, the system shall make no model call, and the ticket view shall say AI is paused and why. | integration |
| TD-008/AC-7 | US-3 | While `ai-triage` is off for a tenant, or `ai-enabled` is off globally, the system shall make no model call for that tenant. | integration |
| TD-008/AC-8 | — | The system shall never show one tenant's suggestion, usage or budget to another tenant. | integration (cross-tenant) |
| TD-008/AC-9 | US-1 | The ticket view shall label the suggestion as AI-generated, with its reason, as text. | E2E + axe |
| TD-008/AC-10 | — | If the provider fails or times out (10 s), the system shall store no suggestion, retry at most once, and leave the ticket fully usable. | integration |

## 4. Out of scope

- Auto-applying suggestions (constitution non-goal: no autonomous AI actions).
- Suggested replies with RAG (TD-009): a course sidebar in M7, not built.
- Tenant-defined categories (the list stays `billing`, `technical`, `account`, `other`).
- Re-triage when a ticket is edited.

## 5. Non-functional notes

- Triage runs in the worker, not the request: ticket creation enqueues it (a row in `ai_triage_jobs`), the worker picks it up. Creation latency is unchanged.
- Metrics: `ai_requests_total{feature,outcome}`, `ai_tokens_total{feature}`, `ai_guardrail_trips_total`, `ai_triage_latency_seconds`. No ticket text in logs or traces.

## 6. Data & privacy

- New personal data collected? **N**. Suggestions hold category, priority and a model-written reason.
- Data shared with third parties? **Y**: masked subject and body go to OrcaRouter or Anthropic (ADR-0004), only for opted-in tenants. The opt-in screen says so before the admin turns it on.

## 7. AI use-case intake

| Item | Answer |
|---|---|
| Purpose | Suggest category + priority for new tickets, for staff |
| Why AI? | Free-text classification: keyword rules can't tell "I was charged twice" (billing) from "charging cable broken" (technical). To confirm in the grill |
| Risk tier | Medium (suggestion only, human applies) |
| EU AI Act | Limited (transparency): labelled as AI |
| Data sent | Subject + body, masked (AC-4). Confidential |
| Retrieval (RAG) | None |
| Tools / actions | None. Output is data, stored as a suggestion |
| Human-in-the-loop | Staff accept or override (AC-2, AC-3) |
| Disclosure | Admin opt-in screen; "AI suggestion" label on the ticket (AC-9) |
| Models | Triage model from `AI_TRIAGE_MODEL` (ADR-0004). Fallback: none, no suggestion |
| Eval criteria | Category accuracy ≥ 85%, priority within one level ≥ 90%, exact priority ≥ 70%, schema-valid 100%, no unmasked PII in prompts 100% |
| Golden set | `evals/triage/golden.jsonl`, 50 synthetic tickets to start, curated by QA |
| Cost budget | 200k tokens per tenant per month; course budget $20/month |
| Kill switch | `ai-enabled` (global) and `ai-triage` (per tenant) |

## 8. Open questions

| # | Question | Owner | Resolved answer |
|---|---|---|---|
| 1 | Should a P1 suggestion notify anyone? | PO | |
| 2 | Show suggestions to customers? | PO | Proposed: never, staff only |
| 3 | Keep suggestions after a ticket is resolved? | PO | Proposed: yes, they're the data for the acceptance metric |

## 9. Approval

| Role | Name | Date |
|---|---|---|
| Product Owner | | |
| Tech Lead | | |
