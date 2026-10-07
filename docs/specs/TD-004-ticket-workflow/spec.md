# TD-004: Ticket workflow: assign, reply, notes, status, audit

| Field | Value |
|---|---|
| Status | **Approved** (brief grill, 2026-10-07) |
| Product Owner / Tech Lead | DeccansoftAITeam |
| Change-risk tier | Medium |
| Threats | TM-008 |

## Status model

```
new ──(staff reply / assign)──► open ◄──(customer reply)── pending_customer
 open ──(staff sets)──► pending_customer        open/pending ──► resolved
 resolved ──(customer reply)──► open   (reopen; TD-007/AC-11 resumes the clock)
```

## Acceptance criteria (EARS)

| ID | Criterion | Layer |
|---|---|---|
| TD-004/AC-1 | When staff assign a ticket to a staff or admin user of the same tenant, the system shall set the assignee; if the user is in another tenant or is a customer, then reject with 422. | API |
| TD-004/AC-2 | When staff post a public reply, the system shall add a message visible to the requester and, if it is the first staff reply, set `first_replied_at`. | API |
| TD-004/AC-3 | When staff post an internal note, the system shall store it and never return it to customers. | API |
| TD-004/AC-4 | When a customer replies to their ticket, the system shall add the message, and if the status is `pending_customer` or `resolved`, set it to `open`. | API |
| TD-004/AC-5 | If a status transition isn't in the status model, then the system shall reject it with 409. | unit + API |
| TD-004/AC-6 | When status, priority, assignee or category changes, the system shall write an audit entry (actor, field, old, new, time). | API |
| TD-004/AC-7 | When status, priority or a reply changes SLA state, the system shall call `compute_deadlines` (TD-005). | integration |
| TD-004/AC-8 | The system shall never accept a message, assignment or status change on another tenant's ticket. | API (cross-tenant) |

## Out of scope

Editing or deleting messages, merging tickets, macros.

## Design notes

`ticket_messages(id, tenant_id, ticket_id, author_id, kind{public,internal}, body, created_at)`. The status machine is a pure function `transition(current, event, actor_role) -> new | error`, with full table-driven unit tests. `audit_log` is append-only (no UPDATE or DELETE grants for `ticketdesk_app`).
