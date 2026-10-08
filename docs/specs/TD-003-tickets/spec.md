# TD-003: Tickets: create, queue, view

| Field | Value |
|---|---|
| Status | **Approved** (brief grill, 2026-10-07) |
| Product Owner / Tech Lead | DeccansoftAITeam |
| Change-risk tier | Medium |
| Related ADRs | ADR-0003 |
| Threats | TM-003, TM-004, TM-006, TM-011, TM-012 |

## Acceptance criteria (EARS)

| ID | Criterion | Layer |
|---|---|---|
| TD-003/AC-1 | When a customer submits a subject (1–200 chars) and body (1–10,000 chars), the system shall create a ticket with status `new`, priority `P3`, the customer as requester, and the next per-tenant ticket number (`#1`, `#2`, …). | API |
| TD-003/AC-2 | When staff create a ticket on behalf of a customer, the system shall allow setting priority and category. | API |
| TD-003/AC-3 | The system shall let customers set neither priority nor category. | API |
| TD-003/AC-4 | When staff request the queue, the system shall return the tenant's tickets, newest first, cursor-paginated, max 100 per page, filterable by status, priority, assignee. | API |
| TD-003/AC-5 | When a customer requests tickets, the system shall return only tickets they requested. | API |
| TD-003/AC-6 | If a customer requests another customer's ticket by ID, then the system shall respond 404. | API |
| TD-003/AC-7 | The system shall render ticket text as sanitized markdown; script, iframe, event-handler attributes and `javascript:` URLs never execute. | E2E |
| TD-003/AC-8 | The system shall never list or return a ticket of another tenant. | API (cross-tenant) |
| TD-003/AC-9 | Ticket create, queue and view pages shall have no serious or critical axe violations. | E2E + axe |

## Out of scope

Attachments (constitution non-goal), search, bulk actions.

## Design notes

`backend/app/features/tickets/`. `tickets(id, tenant_id, number, subject, body, status, priority, category, requester_id, assignee_id, created_at, …)`. Per-tenant number via a `ticket_counters` row locked `FOR UPDATE`. Categories come from a fixed list in v1: `billing`, `technical`, `account`, `other`.
