# TD-002: Roles, admin-created accounts, customer self-registration

| Field | Value |
|---|---|
| Status | **Approved** (brief grill, 2026-10-07) |
| Product Owner / Tech Lead | DeccansoftAITeam |
| Change-risk tier | **High** (authorization) |
| Related ADRs | ADR-0002, ADR-0003 |
| Threats | TM-004, TM-005, TM-013 |

## Roles

| Role | Can |
|---|---|
| `admin` | Everything in their tenant: create and deactivate staff accounts, change roles, SLA settings, AI opt-in, KB |
| `staff` | Work the queue: view all tickets, assign, reply, notes, change status and priority |
| `customer` | Create tickets; see and reply to **only their own** tickets |

## Acceptance criteria (EARS)

| ID | Criterion | Layer |
|---|---|---|
| TD-002/AC-1 | ~~When an admin invites an email as `staff` or `admin`, the system shall return a single-use invite link valid for 7 days, **shown to the admin to copy and share** (never emailed).~~ **Deferred to v2** (2026-10-08) | — |
| TD-002/AC-2 | ~~When an invitee opens a valid invite link and sets a password, the system shall create the user with the invited role.~~ **Deferred to v2** (2026-10-08) | — |
| TD-002/AC-3 | When a visitor registers at `/t/{slug}/auth/register` (with the other auth routes), the system shall create a `customer` user who can log in immediately. | API |
| TD-002/AC-4 | If more than 5 registrations come from one IP in 1 hour for a tenant, then the system shall respond 429 (TM-013). | API |
| TD-002/AC-5 | If a non-admin calls an admin endpoint, then the system shall respond 403. | API |
| TD-002/AC-6 | If a change would leave the tenant with zero active admins, then the system shall reject it. | API |
| TD-002/AC-7 | When an admin changes a user's role or deactivates them, the system shall write an audit entry and revoke the user's refresh tokens. | API |
| TD-002/AC-9 | ~~When an admin requests a password reset for a user, the system shall return a single-use reset link valid for 30 minutes, shown to the admin to share, and invalidate any earlier live reset link.~~ **Deferred to v2** (2026-10-08) | — |
| TD-002/AC-8 | The system shall never return users of another tenant from any endpoint. | API (cross-tenant) |
| TD-002/AC-10 | When an admin creates a `staff` or `admin` account with a name, email and initial password, the system shall create the user ready to log in. (Replaces invite links in v1.) | API |

## Out of scope

Custom roles, teams or groups, customer invitations by staff.

## Design notes

`backend/app/features/users/`. Authorization is a dependency `require_role(...)` on every router plus ownership checks in services (customers). Audit goes through the shared `audit.record()` (created here and reused by TD-004 and TD-007).
