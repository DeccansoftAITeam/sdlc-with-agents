# TD-005: SLA policies and SLA clocks

| Field | Value |
|---|---|
| Status | **Approved** (brief grill, 2026-10-07) |
| Product Owner / Tech Lead | DeccansoftAITeam |
| Change-risk tier | Medium |
| Related | Constitution §8 SLA clock rules; TD-007 grill Q1, Q2, Q5, Q6 |

## Acceptance criteria (EARS)

| ID | Criterion | Layer |
|---|---|---|
| TD-005/AC-1 | When a tenant is created, the system shall create default SLA targets (constitution §8), timezone `UTC` and schedule Mon–Fri 09:00–18:00. | API |
| TD-005/AC-2 | When an admin updates SLA targets, timezone (IANA name) or weekly schedule, the system shall validate and save them, and apply them to **new** tickets only. | API |
| TD-005/AC-3 | The system shall compute `first_response_due_at` and `resolution_due_at` with one pure function `compute_deadlines(created_at, priority, paused_intervals, targets, schedule, tz)`. | unit |
| TD-005/AC-4 | Where priority is P1, the function shall count time 24×7; otherwise only inside the tenant's schedule in its timezone. | unit |
| TD-005/AC-5 | The function shall exclude `pending_customer` intervals from resolution time only. | unit |
| TD-005/AC-6 | The function shall be correct across DST transitions and week boundaries (property-based tests: monotonic in duration; deadline never inside non-working time for P2–P4). | unit (Hypothesis) |
| TD-005/AC-7 | When a ticket is created, changes priority, enters or leaves `pending_customer`, or is reopened, the system shall store the recomputed deadlines. | integration |

## Out of scope

Holiday calendars, per-customer SLAs, SLA reports (later).

## Design notes

`backend/app/features/sla/deadlines.py` is pure, with no I/O and no `now()`. `tickets.paused_intervals` is a JSONB list of `[start, end]`, or a `ticket_pauses` table (decided in T-005-02). `tenant_sla_settings(tenant_id, targets jsonb, timezone, schedule jsonb)`. Targets for existing tickets are snapshotted at creation (AC-2), so changing a policy never makes old tickets breach.
