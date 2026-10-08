"""TD-002 (v1, minimal): customer registration, admin-created accounts, role changes.

All reads and writes run inside the tenant's RLS session; the tenant comes from the token
(admin routes) or the URL slug (public registration), never from the request body.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.core import audit, ratelimit
from app.core.db import tenant_session
from app.core.errors import ProblemError
from app.core.security import Principal, resolve_tenant
from app.features.auth.models import RefreshToken, Role, User
from app.features.auth.passwords import enforce_policy, hash_password
from app.features.users.schemas import RegisterIn, UserCreateIn, UserPatchIn

REGISTRATIONS_PER_IP = (5, 3600.0)  # per tenant, EVERY attempt counts (TD-002/AC-4, limits 409 probing)
EMAIL_TAKEN = ProblemError(409, "Email already registered", "Use another email address.")
NOT_FOUND = ProblemError(404, "Not Found")
LAST_ADMIN = ProblemError(409, "Last admin", "A tenant must keep at least one active admin.")


def _is_email_taken(exc: IntegrityError) -> bool:
    cause = getattr(exc.orig, "__cause__", None)
    return getattr(cause, "constraint_name", None) == "uq_users_tenant_email"


async def _create(
    tenant_id: uuid.UUID, name: str, email: str, password: str, role: str, actor_id: uuid.UUID | None = None
) -> User:
    enforce_policy(password)
    user = User(tenant_id=tenant_id, email=email, name=name, password_hash=hash_password(password), role=role)
    try:
        async with tenant_session(tenant_id) as s:
            s.add(user)
            await s.flush()
            if actor_id is not None:  # admin-created: audited in the SAME transaction
                await audit.record(
                    s,
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    action="user.created",
                    entity="user",
                    entity_id=user.id,
                    data={"role": role},
                )
    except IntegrityError as exc:
        if _is_email_taken(exc):
            raise EMAIL_TAKEN from None
        raise
    return user


async def current_role(principal: Principal) -> str | None:
    """The user's role NOW (None if deactivated or gone): a 15-min access token may be stale."""
    async with tenant_session(principal.tenant_id) as s:
        row = (
            await s.execute(select(User.role, User.is_active).where(User.id == principal.user_id))
        ).one_or_none()
    return row.role if row is not None and row.is_active else None


async def register_customer(slug: str, data: RegisterIn, ip: str) -> User:
    tid = await resolve_tenant(slug)
    key = f"register:{tid}:{ip}"
    ratelimit.hit(key, *REGISTRATIONS_PER_IP)
    return await _create(tid, data.name, data.email, data.password, Role.CUSTOMER)


async def create_account(admin: Principal, data: UserCreateIn) -> User:
    return await _create(admin.tenant_id, data.name, data.email, data.password, data.role, admin.user_id)


async def list_users(admin: Principal) -> list[User]:
    async with tenant_session(admin.tenant_id) as s:
        return list((await s.execute(select(User).order_by(User.created_at, User.email))).scalars())


async def update_user(admin: Principal, user_id: uuid.UUID, change: UserPatchIn) -> User:
    async with tenant_session(admin.tenant_id) as s:
        # Lock every active admin first: two admins demoting each other at the same moment
        # must not both succeed and leave the tenant with none (TD-002/AC-6).
        admins = list(
            (
                await s.execute(
                    select(User.id)
                    .where(User.role == Role.ADMIN, User.is_active.is_(True))
                    .order_by(User.id)
                    .with_for_update()
                )
            ).scalars()
        )
        user = (
            await s.execute(select(User).where(User.id == user_id).with_for_update())
        ).scalar_one_or_none()
        if user is None:
            raise NOT_FOUND  # also for another tenant's user: RLS hides it (TD-002/AC-8)

        new_role = change.role or user.role
        new_active = user.is_active if change.is_active is None else change.is_active
        loses_admin = user.id in admins and (new_role != Role.ADMIN or not new_active)
        if loses_admin and len(admins) == 1:
            raise LAST_ADMIN

        events: list[tuple[str, dict[str, object]]] = []
        if new_role != user.role:
            events.append(("user.role_changed", {"from": user.role, "to": new_role}))
        if new_active != user.is_active:
            events.append(("user.deactivated" if not new_active else "user.reactivated", {}))
        if not events:
            return user

        user.role, user.is_active = new_role, new_active
        for action, data in events:
            await audit.record(
                s,
                tenant_id=admin.tenant_id,
                actor_id=admin.user_id,
                action=action,
                entity="user",
                entity_id=user.id,
                data=data,
            )
        # Sessions issued under the old role/state must not survive the change (TD-002/AC-7).
        await s.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=func.now())
        )
        await s.flush()
        return user
