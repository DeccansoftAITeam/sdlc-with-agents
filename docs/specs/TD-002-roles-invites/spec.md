# TD-002: Staff invites, roles, customer self-registration

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
| `admin` | Everything in their tenant: invite and remove staff, change roles, SLA settings, AI opt-in, KB |
| `staff` | Work the queue: view all tickets, assign, reply, notes, change status and priority |
| `customer` | Create tickets; see and reply to **only their own** tickets |

## Acceptance criteria (EARS)

| ID | Criterion | Layer |
|---|---|---|
| TD-002/AC-1 | When a verified admin invites an email as `staff` or `admin`, the system shall send a single-use invite link valid for 7 days. | API |
| TD-002/AC-2 | When an invitee accepts with a password, the system shall create the user with the invited role and mark the email verified. | API |
| TD-002/AC-3 | When a visitor registers at `/t/{slug}/register`, the system shall create a `customer` user and send a verification email. | API |
| TD-002/AC-4 | While a customer's email is unverified, the system shall block ticket creation. | API |
| TD-002/AC-5 | If a non-admin calls an admin endpoint, then the system shall respond 403. | API |
| TD-002/AC-6 | If a change would leave the tenant with zero active admins, then the system shall reject it. | API |
| TD-002/AC-7 | When an admin changes a user's role or deactivates them, the system shall write an audit entry and revoke the user's refresh tokens. | API |
| TD-002/AC-8 | The system shall never return users of another tenant from any endpoint. | API (cross-tenant) |

## Out of scope

Custom roles, teams or groups, customer invitations by staff.

## Design notes

`backend/app/features/users/`. Authorization is a dependency `require_role(...)` on every router plus ownership checks in services (customers). Audit goes through the shared `audit.record()` (created here and reused by TD-004 and TD-007).
