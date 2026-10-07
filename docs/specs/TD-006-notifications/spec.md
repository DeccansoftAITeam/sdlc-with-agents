# TD-006: In-app notifications

| Field | Value |
|---|---|
| Status | **Approved** (brief grill, 2026-10-07) |
| Product Owner / Tech Lead | DeccansoftAITeam |
| Change-risk tier | Low |

## Acceptance criteria (EARS)

| ID | Criterion | Layer |
|---|---|---|
| TD-006/AC-1 | The system shall provide `notify(tenant_id, user_ids, kind, ticket_id, payload, dedupe_key)` that inserts one notification per user and ignores duplicates of the same `dedupe_key`. | integration |
| TD-006/AC-2 | When a user requests their notifications, the system shall return only their own, newest first, max 50, with the unread count. | API |
| TD-006/AC-3 | When a user marks one or all notifications read, the system shall update only their own. | API |
| TD-006/AC-4 | While the app is open, the web client shall refresh the unread count every 30 s and show it on the bell with an accessible label ("3 unread notifications"). | E2E |
| TD-006/AC-5 | When a ticket is assigned to a user, the system shall notify that user. | integration |
| TD-006/AC-6 | The system shall never return another user's or another tenant's notifications. | API (cross-tenant) |
| TD-006/AC-7 | The system shall delete notifications older than 90 days. | integration |

## Out of scope

Email, push, websockets (polling is enough for v1), notification preferences.

## Design notes

`notifications(id, tenant_id, user_id, kind, ticket_id, payload jsonb, dedupe_key, read_at, created_at, UNIQUE(tenant_id, user_id, dedupe_key))`. TD-007 uses `dedupe_key = "breach:{ticket_id}:{sla_type}"`. Payload holds the ticket number and subject only.
