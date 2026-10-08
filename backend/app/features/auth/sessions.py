"""TD-001 sessions: login, refresh rotation, logout (ADR-0002; TM-001, TM-002, TM-015).

- The tenant is resolved from the URL slug first; users and tokens are read only inside
  that tenant's RLS session.
- Unknown email, wrong password and deactivated user all take the same path: one Argon2
  verification (against a dummy hash if needed) and the same 401 body.
- Refresh tokens: 256-bit random, SHA-256 stored, rotated on every use, 7 days. Presenting
  an already-used or revoked token revokes the whole family; the revocation is COMMITTED
  before the 401 is raised.
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ratelimit
from app.core.db import tenant_session
from app.core.errors import ProblemError
from app.core.security import Principal, issue_access_token, resolve_tenant
from app.features.auth.models import RefreshToken, User
from app.features.auth.passwords import hash_password, verify_password

REFRESH_TTL_DAYS = 7
LOGIN_FAILURES_PER_EMAIL = (5, 60.0)  # 5 failed logins per (tenant, email) per minute
LOGIN_ATTEMPTS_PER_IP = (20, 60.0)  # 20 login attempts per IP per minute
INVALID_CREDENTIALS = ProblemError(401, "Invalid credentials", "Email or password is incorrect.")
INVALID_SESSION = ProblemError(401, "Unauthorized", "Your session has expired. Log in again.")

# Verified against when the email is unknown, so both paths cost one Argon2 verification.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


@dataclass(frozen=True)
class Tokens:
    access: str
    refresh: str


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def _new_refresh(s: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, family: uuid.UUID) -> str:
    raw = secrets.token_urlsafe(32)
    s.add(
        RefreshToken(
            tenant_id=tenant_id,
            user_id=user_id,
            family_id=family,
            token_hash=_digest(raw),
            expires_at=func.now() + func.make_interval(0, 0, 0, REFRESH_TTL_DAYS),
        )
    )
    await s.flush()
    return raw


async def login(slug: str, email: str, password: str, ip: str) -> Tokens:
    ratelimit.hit(f"login-ip:{ip}", *LOGIN_ATTEMPTS_PER_IP)
    fail_key = f"login-fail:{slug}:{email}"
    # Count the attempt BEFORE the slow password check, so parallel requests can't all
    # slip under the limit; undone below if the login succeeds.
    ratelimit.hit(fail_key, *LOGIN_FAILURES_PER_EMAIL)
    tid = await resolve_tenant(slug)
    tokens: Tokens | None = None
    async with tenant_session(tid) as s:
        user = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
        password_ok = verify_password(user.password_hash if user else _DUMMY_HASH, password)
        if user is not None and user.is_active and password_ok:
            refresh = await _new_refresh(s, tid, user.id, uuid.uuid4())
            tokens = Tokens(issue_access_token(user.id, tid, user.role), refresh)
    if tokens is None:
        raise INVALID_CREDENTIALS
    ratelimit.forget_last(fail_key)
    return tokens


async def _revoke_family(s: AsyncSession, family: uuid.UUID) -> None:
    await s.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )


async def refresh(slug: str, raw: str | None) -> Tokens:
    if not raw:
        raise INVALID_SESSION
    tid = await resolve_tenant(slug)
    tokens: Tokens | None = None
    async with tenant_session(tid) as s:
        row = (
            await s.execute(
                select(RefreshToken, (RefreshToken.expires_at > func.now()).label("live"))
                .where(RefreshToken.token_hash == _digest(raw))
                .with_for_update(of=RefreshToken)
            )
        ).one_or_none()
        if row is not None:
            token, live = row
            if token.used_at is not None or token.revoked_at is not None:
                await _revoke_family(s, token.family_id)  # reuse = theft signal (TM-001)
            elif live:
                user = await s.get(User, token.user_id)
                token.used_at = func.now()
                if user is not None and user.is_active:
                    new_raw = await _new_refresh(s, tid, user.id, token.family_id)
                    tokens = Tokens(issue_access_token(user.id, tid, user.role), new_raw)
                else:
                    await _revoke_family(s, token.family_id)
    # The transaction above has committed (including any revocation) before we refuse.
    if tokens is None:
        raise INVALID_SESSION
    return tokens


async def logout(slug: str, raw: str | None) -> None:
    if not raw:
        return
    tid = await resolve_tenant(slug)
    async with tenant_session(tid) as s:
        family = (
            await s.execute(select(RefreshToken.family_id).where(RefreshToken.token_hash == _digest(raw)))
        ).scalar_one_or_none()
        if family is not None:
            await _revoke_family(s, family)


async def me(principal: Principal) -> User:
    async with tenant_session(principal.tenant_id) as s:
        user = await s.get(User, principal.user_id)
    if user is None:
        raise ProblemError(401, "Unauthorized")
    return user
