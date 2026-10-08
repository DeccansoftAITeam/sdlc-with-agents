# TicketDesk v1 — Feature Backlog

The Product Owner owns this list. Each feature gets its own `docs/specs/<ID>-<slug>/spec.md` before work starts. Order = build order.

| ID | Feature | Risk tier | Depends on | Built in |
|---|---|---|---|---|
| TD-001 | Tenant signup, login, JWT refresh, sessions (no email) | **High** (auth) | — | M4 |
| TD-002 | Roles; admin-issued invite and reset links (copy and share); customer self-registration | **High** (authz) | TD-001 | M4 |
| TD-003 | Tickets: create, list (queue), view, with customer/staff visibility rules | Medium | TD-002 | M4 |
| TD-004 | Ticket workflow: assign, reply, internal note, status changes, audit log | Medium | TD-003 | M4 |
| TD-005 | SLA policies per priority and SLA clocks (first response, resolution) | Medium | TD-004 | M4 |
| TD-006 | In-app notifications (bell, unread count) | Low | TD-002 | M4 |
| **TD-007** | **Escalate ticket on SLA breach** (the thread feature) | Medium | TD-005, TD-006 | M4 → M10 |
| TD-008 | AI triage: suggest category + priority (opt-in) | **High** (AI) | TD-003 | M7 |
| TD-009 | Knowledge base + AI suggested reply (RAG, opt-in) | **High** (AI) | TD-004 | M7 |
| TD-012 | Customer satisfaction (CSAT) rating | Medium | TD-004 | M12 capstone |

The course works through **TD-007** in full detail in M2. The other specs are produced the same way (`/spec-draft` → `/grill` → approve) and are in the reference solution so M4 has something to build on.
