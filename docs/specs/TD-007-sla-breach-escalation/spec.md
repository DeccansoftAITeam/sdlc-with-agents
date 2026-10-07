# TD-007: Escalate ticket on SLA breach

| Field | Value |
|---|---|
| Status | **Grilled** (2026-10-07; approval pending with `tasks.md`) |
| Product Owner | DeccansoftAITeam |
| Tech Lead | DeccansoftAITeam |
| Change-risk tier | Medium (application code; new columns only, no auth or PII) |
| Feature flag | `sla-breach-escalation` (owner: TL, removal date: 2026-12-31) |
| Related ADRs | ADR-0003 (multi-tenancy) |
| Depends on | TD-005 (SLA clocks, tenant business hours), TD-006 (in-app notifications) |
| Grill log | `docs/grill-logs/2026-10-07-td007.md` |

## 1. Problem & outcome

Support staff can't see which tickets have missed their SLA. Breaches are found late, by customers complaining. Tenants promise SLAs to their customers (constitution §8), so missed breaches are broken promises.

Success measure: 99.9% of breaches flagged and notified within 60 s (SLO "SLA timer accuracy"), and a 30% drop in breached tickets per tenant within 4 weeks of enabling.

## 2. User stories

- **US-1** As **support staff**, I want a breached ticket clearly flagged and floated to the top of my queue while it still needs action, so that I work on it first.
- **US-2** As the **assignee**, I want an in-app notification when my ticket breaches, so that I find out without watching the queue.
- **US-3** As a **tenant admin**, I want to be notified of every breach in my tenant, so that I can step in.
- **US-4** As a **tenant admin**, I want a permanent record of when and which SLA was breached, so that I can review performance.

## 3. Definitions

- **SLA clocks** (owned by TD-005): `first_response_due_at` and `resolution_due_at`, computed by one pure function `compute_deadlines(ticket, policy, schedule)`. Time counts **in tenant business hours** (tenant timezone + weekly schedule) for P2–P4, and **24×7 for P1**. The resolution clock **pauses** while the status is `pending_customer`. The first-response clock never pauses. Deadlines are always computed **from ticket creation minus paused time**, never restarted.
- **Breached** (history): `first_response_breached_at` / `resolution_breached_at` is set. It's permanent and never cleared.
- **Breach-active** (queue state): the ticket is open, and a breached SLA is still unmet. First response is unmet until the first staff reply; resolution is unmet until the ticket is resolved.

## 4. Acceptance criteria (EARS)

| ID | Story | Criterion (EARS) | Test layer |
|---|---|---|---|
| TD-007/AC-1 | US-1 | When a ticket's `first_response_due_at` passes with no staff reply, the system shall set `first_response_breached_at` within 60 s. | integration |
| TD-007/AC-2 | US-1 | When a ticket's `resolution_due_at` passes while the ticket is not resolved, the system shall set `resolution_breached_at` within 60 s. | integration |
| TD-007/AC-3 | US-1 | While a ticket is breach-active, the queue shall list it above all tickets that are not breach-active, ordered by earliest breach time first. | API + E2E |
| TD-007/AC-4 | US-2 | When an **assigned** ticket breaches, the system shall create an in-app notification for the assignee. | integration |
| TD-007/AC-5 | US-3 | When a ticket breaches, the system shall create an in-app notification for every admin of the ticket's tenant. | integration |
| TD-007/AC-6 | US-4 | When a ticket breaches, the system shall write an audit entry with ticket ID, SLA type, deadline and detection time. | integration |
| TD-007/AC-7 | US-2 | The system shall create at most one breach record, one audit entry and **one notification per user** for each (ticket, SLA type) breach, including when the assignee is also an admin and when the detector runs repeatedly or concurrently. | integration |
| TD-007/AC-8 | — | The system shall never flag, list or notify a ticket to a user of a different tenant. | integration (cross-tenant) |
| TD-007/AC-9 | US-1 | The system shall show a breach badge with SLA type and time since breach, using a text label and not colour alone, only while the ticket is breach-active. | E2E + axe |
| TD-007/AC-10 | US-1 | While a ticket is `pending_customer`, the system shall not breach its resolution SLA, and on resume shall extend `resolution_due_at` by the paused business time. | unit + integration |
| TD-007/AC-11 | US-4 | When a resolved ticket is reopened, the system shall resume its resolution clock from the time already consumed and shall not clear any existing breach record. | integration |
| TD-007/AC-12 | US-1 | When staff send the first reply to a first-response-breached ticket, the system shall stop treating that breach as active while keeping `first_response_breached_at`. | integration |
| TD-007/AC-13 | US-1 | When a ticket's priority changes, the system shall recompute its deadlines from creation minus paused time using the new priority's targets, and shall not clear an existing breach record. | unit + integration |
| TD-007/AC-14 | — | While the flag `sla-breach-escalation` is off for a tenant, the system shall not flag, float or notify breaches for that tenant. | integration |

## 5. Out of scope

- Changing priority, reassigning or auto-replying on breach (constitution non-goal).
- Email or webhook notifications (constitution non-goal; in-app only).
- "About to breach" warnings.
- Holiday calendars (v1 uses the weekly schedule only).
- Notifying all staff on unassigned breaches (admins cover it, grill Q4).

## 6. Non-functional notes

- Detection within 60 s is an SLO. Sweep every 30 s; metric `sla_sweep_duration_seconds`, alert when p95 is above 5 s; metric `sla_breaches_detected_total{sla_type}`.
- Capacity: 100 tenants × 10k open tickets in under 5 s per sweep. Revisit above about 1k tenants.

## 7. Data & privacy

- New personal data collected? **N**. Notifications reference ticket number and subject only.
- New data shared with third parties? **N**.

## 8. AI use-case intake

Not applicable. (TD-008 AI triage may change priority; AC-13 covers that path like any other priority change.)

## 9. Open questions

| # | Question | Owner | Resolved answer |
|---|---|---|---|
| 1 | Unassigned ticket breaches: who is notified? | PO | Admins only (AC-4, AC-5); at most once per user (AC-7) |
| 2 | Calendar vs business hours? | PO | Tenant business hours for P2–P4; P1 24×7; no holidays in v1 (§3) |
| 3 | Does a breach flag clear? | PO | Never. Breach-active ends on reply or resolve; reopen resumes (AC-11, AC-12) |
| 4 | How is the detector run? | TL | 30 s sweep, advisory lock, per-tenant loop under RLS (design §4) |
| 5 | Clock paused while `pending_customer`? | PO | Resolution clock only (AC-10) |

## 10. Approval

| Role | Name | Date |
|---|---|---|
| Product Owner | | |
| Tech Lead | | |
