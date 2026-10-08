"""TD-001 signup and email verification (T-001-02).

Rules this module relies on (see .agents/progress/T-001-02.md and ADR-0002/0003):
- The tenant is resolved from the URL slug BEFORE any token lookup; token tables are
  only read inside that tenant's RLS session.
- Tokens: 256-bit random, URL-safe; only the SHA-256 hex digest is stored; single use,
  consumed atomically; 30-minute lifetime; one live token per user+purpose (DB index).
- Responses that could reveal whether an email exists are identical (TM-015).
"""

import hashlib
import secrets
import uuid

from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import sessionmaker, system_session, tenant_session
from app.core.email import EmailMessage, EmailSender
from app.core.errors import ProblemError
from app.features.auth.models import EmailToken, EmailTokenPurpose, Role, User
from app.features.auth.passwords import BreachedPasswordChecker, enforce_policy, hash_password
from app.features.auth.schemas import SignupIn

RESERVED_SLUGS = frozenset({"api", "admin", "t", "login", "signup", "static", "health"})
LINK_LIFETIME = "30 minutes"
INVALID_LINK = ProblemError(400, "Invalid or expired link", "Request a new verification email.")


def new_token() -> tuple[str, str]:
    """Return (raw token for the link, SHA-256 hex digest for storage)."""
    raw = secrets.token_urlsafe(32)
    return raw, _digest(raw)


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def resolve_tenant(slug: str) -> uuid.UUID:
    async with system_session() as s:
        tid = (await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one()
    if tid is None:
        raise ProblemError(404, "Not Found")
    return uuid.UUID(str(tid))


async def _issue_verify_token(s: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID) -> str:
    """Consume any live verify token for the user, then create a new one (one live link)."""
    await s.execute(
        update(EmailToken)
        .where(
            EmailToken.user_id == user_id,
            EmailToken.purpose == EmailTokenPurpose.VERIFY,
            EmailToken.used_at.is_(None),
        )
        .values(used_at=text("now()"))
    )
    raw, digest = new_token()
    s.add(
        EmailToken(
            tenant_id=tenant_id,
            user_id=user_id,
            purpose=EmailTokenPurpose.VERIFY,
            token_hash=digest,
            expires_at=text(f"now() + interval '{LINK_LIFETIME}'"),
        )
    )
    await s.flush()
    return raw


async def _send_verification(sender: EmailSender, to: str, slug: str, raw: str) -> None:
    link = f"{get_settings().web_base_url}/t/{slug}/verify?token={raw}"
    await sender.send(
        EmailMessage(
            to=to,
            subject="Verify your TicketDesk email",
            body=f"Confirm your email address within 30 minutes:\n\n{link}\n\n"
            "If you didn't sign up, ignore this email.",
        )
    )


async def signup(data: SignupIn, checker: BreachedPasswordChecker, sender: EmailSender) -> str:
    """Create tenant + first admin + verify token in ONE transaction, then send the email."""
    if data.slug in RESERVED_SLUGS:
        raise ProblemError(422, "Slug not available", "This address is reserved.")
    await enforce_policy(data.password, checker)
    password_hash = hash_password(data.password)
    try:
        async with sessionmaker()() as s, s.begin():
            tid = uuid.UUID(
                str(
                    (
                        await s.execute(
                            text("SELECT create_tenant(:slug, :name)"),
                            {"slug": data.slug, "name": data.company_name},
                        )
                    ).scalar_one()
                )
            )
            # Same transaction, now scoped to the new tenant so RLS applies to the inserts.
            await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})
            admin = User(
                tenant_id=tid,
                email=data.email,
                name=data.admin_name,
                password_hash=password_hash,
                role=Role.ADMIN,
            )
            s.add(admin)
            await s.flush()
            raw = await _issue_verify_token(s, tid, admin.id)
    except IntegrityError as exc:
        if "tenants_slug_key" in str(exc.orig):
            raise ProblemError(409, "Slug not available", "Choose another address.") from None
        raise
    await _send_verification(sender, data.email, data.slug, raw)
    return data.slug


async def verify_email(slug: str, raw: str) -> None:
    tid = await resolve_tenant(slug)
    async with tenant_session(tid) as s:
        user_id = (
            await s.execute(
                update(EmailToken)
                .where(
                    EmailToken.token_hash == _digest(raw),
                    EmailToken.purpose == EmailTokenPurpose.VERIFY,
                    EmailToken.used_at.is_(None),
                    EmailToken.expires_at > text("now()"),
                )
                .values(used_at=text("now()"))
                .returning(EmailToken.user_id)
            )
        ).scalar_one_or_none()
        if user_id is None:
            raise INVALID_LINK
        await s.execute(
            update(User)
            .where(User.id == user_id, User.email_verified_at.is_(None))
            .values(email_verified_at=text("now()"))
        )


async def resend_verification(slug: str, email: str, sender: EmailSender) -> None:
    """Always succeeds from the caller's view; only unverified, active users get an email."""
    tid = await resolve_tenant(slug)
    raw: str | None = None
    async with tenant_session(tid) as s:
        user = (
            await s.execute(
                select(User).where(
                    User.email == email, User.email_verified_at.is_(None), User.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()
        if user is not None:
            raw = await _issue_verify_token(s, tid, user.id)
    if raw is not None:
        await _send_verification(sender, email, slug, raw)
