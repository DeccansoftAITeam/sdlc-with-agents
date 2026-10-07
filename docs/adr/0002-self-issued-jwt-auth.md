# ADR-0002: Self-issued JWT authentication with per-tenant identity

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-07 |
| Deciders | Tech Lead, Product Owner |
| Consulted | Security reviewer (rotating TL) |
| Deviates from org default? | No (no org default for auth) |
| Related spec(s) | TD-001, TD-002 |

## Context and problem statement

The PO ruled out SSO and external identity providers for v1 (constitution non-goal). Tenants are self-serve (grill Q1). Identity is **per tenant**: the same email in two tenants is two users (grill Q2). We must meet ASVS L2 for authentication and session management (V2, V3) while owning the code.

## Decision drivers

- ASVS L2; threats TM-001, TM-002, TM-013, TM-014, TM-015
- Stateless API auth that carries `tenant_id` and `role`
- Ability to revoke sessions (password reset, stolen token)

## Considered options

1. **Self-issued JWT access token + rotating opaque refresh token**
2. Server-side sessions with cookies only
3. A hosted identity provider (Entra External ID, Auth0, Clerk): excluded by the PO

## Decision outcome

**Option 1.**

| Item | Choice |
|---|---|
| Password hashing | Argon2id (`argon2-cffi`, OWASP parameters), breached-password check (k-anonymity range API, fail-open with a log) |
| Access token | JWT, **EdDSA (Ed25519)**, 15 min, claims `sub`, `tid` (tenant), `role`, `jti`; algorithm pinned on verify; signing key in Key Vault, read with managed identity |
| Refresh token | Opaque 256-bit random value, **stored hashed**, 7 days, rotated on every use; **reuse of an old token revokes the whole family** (TM-001) |
| Transport (web) | Access token in memory; refresh token in an `HttpOnly; Secure; SameSite=Strict` cookie scoped to `/api/auth/refresh` |
| Identity | `users UNIQUE (tenant_id, email)`; login requires the tenant slug (`/t/{slug}/login`) |
| Verify / reset tokens | 256-bit random, stored hashed, single use, 30 min (TM-014); a reset revokes all refresh families |
| Enumeration | Identical responses and timing for unknown emails (TM-015) |
| Rate limits | Login 5/min per (tenant, email) + 20/min per IP; signup 3/hour per IP (TM-002, TM-013) |

### Consequences

- Good: no third-party identity cost; everything is testable in CI.
- Bad: we own high-risk code. Every auth PR is **High** tier (2 approvals including TL + `security-reviewer` subagent).
- Bad: no MFA in v1. It's a known gap against ASVS L2 V2.8, recorded as an accepted risk with a v2 follow-up.

### Confirmation

Tests named in the threat model: `test_refresh_reuse_revokes_family`, `test_login_rate_limit`, `test_reset_token_single_use_and_expiry`, `test_no_account_enumeration`, plus the security-reviewer pass on every auth PR.
