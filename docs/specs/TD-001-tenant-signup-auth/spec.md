# TD-001: Tenant signup, login, refresh, sessions

| Field | Value |
|---|---|
| Status | **Approved** (brief grill, 2026-10-07) |
| Product Owner / Tech Lead | DeccansoftAITeam |
| Change-risk tier | **High** (authentication) |
| Feature flag | none (foundation) |
| Related ADRs | ADR-0002, ADR-0003 |
| Threats | TM-001, TM-002, TM-013, TM-014, TM-015 |
| Grill log | `docs/grill-logs/2026-10-07-foundations.md` |

## User stories

- **US-1** As a company, I want to sign up and get my own TicketDesk tenant, so that my team can start supporting customers.
- **US-2** As any user, I want to log in to my tenant and stay logged in safely.
- **US-3** As any user, I want my sessions ended when my password is reset, so that a stolen session stops working.

## Acceptance criteria (EARS)

| ID | Criterion | Layer |
|---|---|---|
| TD-001/AC-1 | When a visitor submits company name, slug, name, email and password, the system shall create the tenant and its first **admin** user, ready to log in immediately (no email verification). | API |
| TD-001/AC-2 | If the slug is taken, reserved (`api`, `admin`, `t`, `login`, `signup`, `static`, `health`), or not `^[a-z0-9-]{3,40}$`, then the system shall reject the signup with a Problem Details error. | API |
| TD-001/AC-3 | If the password is shorter than 12 characters or appears in the bundled common-password list, then the system shall reject it. | API |
| TD-001/AC-4 | When a user logs in at `/t/{slug}` with valid credentials, the system shall return a 15-min access token (claims `sub`, `tid`, `role`, `jti`) and set a rotating refresh cookie. | API |
| TD-001/AC-5 | When a refresh token is used, the system shall issue a new pair and invalidate the old refresh token. | API |
| TD-001/AC-6 | If an already-used refresh token is presented, then the system shall revoke the whole token family and return 401. | API |
| TD-001/AC-7 | The system shall return identical responses and similar timing for unknown and known emails on login failure. | API |
| TD-001/AC-8 | If more than 5 failed logins occur for a (tenant, email) in 1 minute, more than 20 login attempts come from one IP in 1 minute, or more than 3 successful signups come from one IP in 1 hour, then the system shall respond 429 with `Retry-After`. | API |
| TD-001/AC-9 | ~~Email verification~~ (removed 2026-10-08: no email) | — |
| TD-001/AC-10 | ~~Reset revokes sessions~~ **Deferred to v2** with admin-issued reset links (2026-10-08) | — |
| TD-001/AC-11 | ~~Unverified admin restrictions~~ (removed 2026-10-08: no verification) | — |
| TD-001/AC-12 | If the URL slug does not match the access token's tenant, then the system shall respond 404. | API |

## Out of scope

MFA (ADR-0002 accepted risk), SSO, tenant deletion (later), "remember me" beyond 7 days, **any email** (constitution amendment 2026-10-08).

## Design notes

Feature folder `backend/app/features/auth/`. Tables: `tenants` (not tenant-owned; accessed through `tenant_repo` only), `users` (RLS, `UNIQUE(tenant_id, email)`), `refresh_tokens` (hashed, `family_id`), `email_tokens` (hashed, purpose, expiry; **unused in v1**: reserved for admin-issued invite/reset links in v2). No email is ever sent. Signing key from Key Vault via the `KeyProvider` port; a file key locally.
