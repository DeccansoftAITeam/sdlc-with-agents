"""TD-002 acceptance tests for PR B: roles, admin-created accounts, customer registration.

Written BEFORE the implementation (acceptance-tdd). API-level only, except where the
database is inspected to prove an audit entry or token revocation happened.
"""

import uuid
from http.cookies import SimpleCookie
from typing import Any

import httpx
import pytest
from sqlalchemy import text

from app.core.db import system_session, tenant_session

PASSWORD = "a-long-unique-passphrase"
STAFF_PASSWORD = "another-long-passphrase"


async def _tenant(client: httpx.AsyncClient) -> str:
    slug = f"acme-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/signup",
        json={
            "company_name": "Acme",
            "slug": slug,
            "admin_name": "Ada",
            "email": "ada@example.com",
            "password": PASSWORD,
        },
    )
    assert r.status_code == 201, r.text
    return slug


async def _login(client: httpx.AsyncClient, slug: str, email: str, password: str) -> httpx.Response:
    return await client.post(f"/t/{slug}/auth/login", json={"email": email, "password": password})


async def _auth(
    client: httpx.AsyncClient, slug: str, email: str = "ada@example.com", password: str = PASSWORD
) -> dict[str, str]:
    r = await _login(client, slug, email, password)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _create(client: httpx.AsyncClient, slug: str, admin: dict[str, str], **body: Any) -> httpx.Response:
    payload = {"name": "Sam Staff", "email": "sam@example.com", "password": STAFF_PASSWORD, "role": "staff"}
    payload.update(body)
    return await client.post(f"/t/{slug}/users", json=payload, headers=admin)


async def _tenant_id(slug: str) -> uuid.UUID:
    async with system_session() as s:
        return uuid.UUID(
            str((await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one())
        )


# --- AC-10: admins create staff/admin accounts ----------------------------------------------


@pytest.mark.parametrize("role", ["staff", "admin"])
async def test_td002_ac10_admin_creates_account_ready_to_log_in(client: httpx.AsyncClient, role: str) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    r = await _create(client, slug, admin, role=role, email="Sam@Example.com")
    assert r.status_code == 201
    assert r.json()["role"] == role and r.json()["email"] == "sam@example.com"
    assert "password" not in r.json() and "password_hash" not in r.json()
    me = await client.get(
        f"/t/{slug}/me", headers=await _auth(client, slug, "sam@example.com", STAFF_PASSWORD)
    )
    assert me.json()["role"] == role


async def test_td002_ac10_duplicate_email_is_409(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    assert (await _create(client, slug, admin)).status_code == 201
    r = await _create(client, slug, admin)
    assert r.status_code == 409 and r.headers["content-type"] == "application/problem+json"


async def test_td002_ac10_weak_or_common_password_rejected(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    assert (await _create(client, slug, admin, password="short")).status_code == 422
    assert (await _create(client, slug, admin, password="Password1234")).status_code == 422


async def test_td002_ac10_admin_cannot_create_customers_or_unknown_roles(client: httpx.AsyncClient) -> None:
    """Customers register themselves (AC-3); the create endpoint is for staff and admins only."""
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    for role in ("customer", "superuser"):
        assert (await _create(client, slug, admin, role=role)).status_code == 422


# --- AC-3 / AC-4: customer self-registration ---------------------------------------------------


async def test_td002_ac3_customer_registers_and_logs_in_immediately(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    r = await client.post(
        f"/t/{slug}/auth/register",
        json={"name": "Cara", "email": "Cara@Example.com", "password": STAFF_PASSWORD},
    )
    assert r.status_code == 201
    me = await client.get(
        f"/t/{slug}/me", headers=await _auth(client, slug, "cara@example.com", STAFF_PASSWORD)
    )
    assert me.json()["role"] == "customer"


async def test_td002_ac3_register_rejects_duplicate_and_weak(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    body = {"name": "Cara", "email": "cara@example.com", "password": STAFF_PASSWORD}
    assert (await client.post(f"/t/{slug}/auth/register", json=body)).status_code == 201
    assert (await client.post(f"/t/{slug}/auth/register", json=body)).status_code == 409
    weak = body | {"email": "dan@example.com", "password": "Password1234"}
    assert (await client.post(f"/t/{slug}/auth/register", json=weak)).status_code == 422


async def test_td002_ac3_register_at_unknown_tenant_is_404(client: httpx.AsyncClient) -> None:
    r = await client.post(
        "/t/no-such-tenant/auth/register",
        json={"name": "C", "email": "c@example.com", "password": STAFF_PASSWORD},
    )
    assert r.status_code == 404


async def test_td002_ac4_sixth_registration_from_one_ip_is_429(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    for i in range(5):
        r = await client.post(
            f"/t/{slug}/auth/register",
            json={"name": "C", "email": f"c{i}@example.com", "password": STAFF_PASSWORD},
        )
        assert r.status_code == 201
    r = await client.post(
        f"/t/{slug}/auth/register", json={"name": "C", "email": "c9@example.com", "password": STAFF_PASSWORD}
    )
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0


# --- AC-5: admin endpoints need the admin role ------------------------------------------------


@pytest.mark.parametrize("role", ["staff", "customer"])
async def test_td002_ac5_non_admins_get_403(client: httpx.AsyncClient, role: str) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    if role == "staff":
        await _create(client, slug, admin)
    else:
        await client.post(
            f"/t/{slug}/auth/register",
            json={"name": "Sam", "email": "sam@example.com", "password": STAFF_PASSWORD},
        )
    user = await _auth(client, slug, "sam@example.com", STAFF_PASSWORD)
    assert (await client.get(f"/t/{slug}/users", headers=user)).status_code == 403
    assert (await _create(client, slug, user, email="x@example.com")).status_code == 403


async def test_td002_ac5_no_token_is_401(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    assert (await client.get(f"/t/{slug}/users")).status_code == 401


# --- AC-6 / AC-7: role changes, deactivation, last admin -------------------------------------


async def _user_id(client: httpx.AsyncClient, slug: str, admin: dict[str, str], email: str) -> str:
    users = (await client.get(f"/t/{slug}/users", headers=admin)).json()
    return next(u["id"] for u in users if u["email"] == email)


async def test_td002_ac6_last_admin_cannot_be_demoted_or_deactivated(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    me = await _user_id(client, slug, admin, "ada@example.com")
    for change in ({"role": "staff"}, {"is_active": False}):
        r = await client.patch(f"/t/{slug}/users/{me}", json=change, headers=admin)
        assert r.status_code == 409 and r.headers["content-type"] == "application/problem+json"


async def test_td002_ac6_admin_can_be_demoted_when_another_admin_exists(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    await _create(client, slug, admin, role="admin")
    me = await _user_id(client, slug, admin, "ada@example.com")
    r = await client.patch(f"/t/{slug}/users/{me}", json={"role": "staff"}, headers=admin)
    assert r.status_code == 200 and r.json()["role"] == "staff"


async def test_td002_ac7_role_change_is_audited_and_revokes_sessions(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    await _create(client, slug, admin)
    login = await _login(client, slug, "sam@example.com", STAFF_PASSWORD)
    jar: SimpleCookie = SimpleCookie()
    jar.load(login.headers["set-cookie"])
    sam_refresh = jar["refresh_token"].value
    sam = await _user_id(client, slug, admin, "sam@example.com")

    r = await client.patch(f"/t/{slug}/users/{sam}", json={"role": "admin"}, headers=admin)
    assert r.status_code == 200

    refreshed = await client.post(
        f"/t/{slug}/auth/refresh", headers={"Cookie": f"refresh_token={sam_refresh}"}
    )
    assert refreshed.status_code == 401  # old session gone; Sam logs in again with the new role
    async with tenant_session(await _tenant_id(slug)) as s:
        row = (
            await s.execute(
                text("SELECT action, entity_id, data FROM audit_log WHERE action = 'user.role_changed'")
            )
        ).one()
    assert row.action == "user.role_changed" and str(row.entity_id) == sam
    assert row.data == {"from": "staff", "to": "admin"}


async def test_td002_ac7_deactivation_is_audited_and_blocks_login(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    await _create(client, slug, admin)
    sam = await _user_id(client, slug, admin, "sam@example.com")
    r = await client.patch(f"/t/{slug}/users/{sam}", json={"is_active": False}, headers=admin)
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert (await _login(client, slug, "sam@example.com", STAFF_PASSWORD)).status_code == 401
    async with tenant_session(await _tenant_id(slug)) as s:
        actions = (await s.execute(text("SELECT action FROM audit_log ORDER BY created_at"))).scalars().all()
    assert actions == ["user.created", "user.deactivated"]  # creation is audited too


async def test_td002_ac7_audit_log_is_append_only() -> None:
    """The runtime role may insert audit rows but never change or delete them."""
    async with system_session() as s:
        tid = (
            await s.execute(text("SELECT create_tenant(:s, 'X')"), {"s": f"x-{uuid.uuid4().hex[:8]}"})
        ).scalar_one()
    from sqlalchemy.exc import DBAPIError

    for sql in ("UPDATE audit_log SET action = 'x'", "DELETE FROM audit_log", "TRUNCATE audit_log"):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with tenant_session(uuid.UUID(str(tid))) as s:
                await s.execute(text(sql))


# --- AC-8: never another tenant's users -------------------------------------------------------


async def test_td002_ac8_user_list_and_patch_are_tenant_scoped(client: httpx.AsyncClient) -> None:
    slug_a, slug_b = await _tenant(client), await _tenant(client)
    admin_a, admin_b = await _auth(client, slug_a), await _auth(client, slug_b)
    await _create(client, slug_a, admin_a)
    sam_a = await _user_id(client, slug_a, admin_a, "sam@example.com")

    emails_b = [u["email"] for u in (await client.get(f"/t/{slug_b}/users", headers=admin_b)).json()]
    assert emails_b == ["ada@example.com"]
    r = await client.patch(f"/t/{slug_b}/users/{sam_a}", json={"is_active": False}, headers=admin_b)
    assert r.status_code == 404
    # and tenant A's token can't be used at tenant B's address (AC-12 of TD-001)
    assert (await client.get(f"/t/{slug_b}/users", headers=admin_a)).status_code == 404


async def test_td002_ac5_demoted_admin_loses_admin_powers_immediately(client: httpx.AsyncClient) -> None:
    """Security finding: a still-valid access token must not keep admin powers after demotion."""
    slug = await _tenant(client)
    ada = await _auth(client, slug)
    await _create(client, slug, ada, role="admin", email="bea@example.com")
    bea = await _auth(client, slug, "bea@example.com", STAFF_PASSWORD)
    ada_id = await _user_id(client, slug, ada, "ada@example.com")
    assert (
        await client.patch(f"/t/{slug}/users/{ada_id}", json={"role": "staff"}, headers=bea)
    ).status_code == 200
    # Ada's access token still says "admin" for up to 15 minutes, but the server re-checks.
    assert (await client.get(f"/t/{slug}/users", headers=ada)).status_code == 403


async def test_td002_ac4_failed_registrations_count_too(client: httpx.AsyncClient) -> None:
    """Security finding: 409 probing for existing emails is rate-limited like any attempt."""
    slug = await _tenant(client)
    body = {"name": "C", "email": "ada@example.com", "password": STAFF_PASSWORD}  # existing email
    for _ in range(5):
        assert (await client.post(f"/t/{slug}/auth/register", json=body)).status_code == 409
    assert (await client.post(f"/t/{slug}/auth/register", json=body)).status_code == 429


async def test_td002_ac6_concurrent_demotions_keep_one_admin(client: httpx.AsyncClient) -> None:
    """Code review: two admins demoting each other at the same instant must not leave zero admins."""
    import asyncio

    slug = await _tenant(client)
    ada = await _auth(client, slug)
    await _create(client, slug, ada, role="admin", email="bea@example.com")
    bea = await _auth(client, slug, "bea@example.com", STAFF_PASSWORD)
    ada_id = await _user_id(client, slug, ada, "ada@example.com")
    bea_id = await _user_id(client, slug, ada, "bea@example.com")
    results = await asyncio.gather(
        client.patch(f"/t/{slug}/users/{bea_id}", json={"role": "staff"}, headers=ada),
        client.patch(f"/t/{slug}/users/{ada_id}", json={"role": "staff"}, headers=bea),
    )
    assert sorted(r.status_code for r in results) in ([200, 403], [200, 409])
    async with tenant_session(await _tenant_id(slug)) as s:
        admins = (
            await s.execute(text("SELECT count(*) FROM users WHERE role = 'admin' AND is_active"))
        ).scalar_one()
    assert admins == 1


async def test_td002_ac7_noop_change_writes_nothing(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    admin = await _auth(client, slug)
    await _create(client, slug, admin)
    sam = await _user_id(client, slug, admin, "sam@example.com")
    r = await client.patch(f"/t/{slug}/users/{sam}", json={"role": "staff", "is_active": True}, headers=admin)
    assert r.status_code == 200
    async with tenant_session(await _tenant_id(slug)) as s:
        actions = (await s.execute(text("SELECT action FROM audit_log"))).scalars().all()
    assert actions == ["user.created"]


async def test_td002_ac6_reactivated_admin_counts_again(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    ada = await _auth(client, slug)
    await _create(client, slug, ada, role="admin", email="bea@example.com")
    bea_id = await _user_id(client, slug, ada, "bea@example.com")
    ada_id = await _user_id(client, slug, ada, "ada@example.com")
    assert (
        await client.patch(f"/t/{slug}/users/{bea_id}", json={"is_active": False}, headers=ada)
    ).status_code == 200
    assert (
        await client.patch(f"/t/{slug}/users/{ada_id}", json={"role": "staff"}, headers=ada)
    ).status_code == 409
    assert (
        await client.patch(f"/t/{slug}/users/{bea_id}", json={"is_active": True}, headers=ada)
    ).status_code == 200
    assert (
        await client.patch(f"/t/{slug}/users/{ada_id}", json={"role": "staff"}, headers=ada)
    ).status_code == 200
