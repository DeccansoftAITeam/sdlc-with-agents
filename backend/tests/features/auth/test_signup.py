"""TD-001 acceptance tests for T-001-02: signup, slug rules and password rules.

As amended 2026-10-08: no email anywhere. A new admin can log in immediately.
These talk to the API only, the way a browser would; the database is inspected only to
prove what was stored.
"""

import uuid
from typing import Any

import httpx
import pytest
from sqlalchemy import text

from app.core.db import system_session, tenant_session

PASSWORD = "a-long-unique-passphrase"


def _slug() -> str:
    return f"acme-{uuid.uuid4().hex[:8]}"


def _signup_body(**overrides: Any) -> dict[str, Any]:
    body = {
        "company_name": "Acme Support",
        "slug": _slug(),
        "admin_name": "Ada Admin",
        "email": "Ada@Example.com",
        "password": PASSWORD,
    }
    body.update(overrides)
    return body


async def _tenant_id(slug: str) -> uuid.UUID | None:
    async with system_session() as s:
        tid = (await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one()
    return None if tid is None else uuid.UUID(str(tid))


# --- AC-1: signup creates the tenant and its first admin, usable immediately -------------


async def test_td001_ac1_signup_creates_tenant_and_admin(client: httpx.AsyncClient) -> None:
    body = _signup_body()
    r = await client.post("/signup", json=body)
    assert r.status_code == 201
    assert r.json() == {"tenant_slug": body["slug"]}

    tid = await _tenant_id(body["slug"])
    assert tid is not None
    async with tenant_session(tid) as s:
        row = (await s.execute(text("SELECT email, role, is_active, password_hash FROM users"))).one()
    assert row.email == "ada@example.com"  # normalised
    assert row.role == "admin"
    assert row.is_active  # no verification step: ready to log in (T-001-03)
    assert row.password_hash.startswith("$argon2id$")  # ADR-0002


async def test_td001_ac1_signup_creates_no_tokens(client: httpx.AsyncClient) -> None:
    """No email verification: nothing is issued that would need to be sent somewhere."""
    body = _signup_body()
    await client.post("/signup", json=body)
    tid = await _tenant_id(body["slug"])
    assert tid is not None
    async with tenant_session(tid) as s:
        assert (await s.execute(text("SELECT count(*) FROM email_tokens"))).scalar_one() == 0


# --- AC-2: slug rules --------------------------------------------------------------------


async def test_td001_ac2_taken_slug_rejected(client: httpx.AsyncClient) -> None:
    body = _signup_body()
    assert (await client.post("/signup", json=body)).status_code == 201
    r = await client.post("/signup", json=_signup_body(slug=body["slug"], email="other@example.com"))
    assert r.status_code == 409
    assert r.headers["content-type"] == "application/problem+json"


# "t" is also reserved but is already rejected by the format rule (min 3 chars).
@pytest.mark.parametrize("slug", ["api", "admin", "login", "signup", "static", "health"])
async def test_td001_ac2_reserved_slug_rejected(client: httpx.AsyncClient, slug: str) -> None:
    r = await client.post("/signup", json=_signup_body(slug=slug))
    assert r.status_code == 422
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["title"] == "Slug not available"


@pytest.mark.parametrize("slug", ["ab", "Has-Caps", "under_score", "x" * 41, "spa ce", "t"])
async def test_td001_ac2_malformed_slug_rejected(client: httpx.AsyncClient, slug: str) -> None:
    r = await client.post("/signup", json=_signup_body(slug=slug))
    assert r.status_code == 422
    assert r.headers["content-type"] == "application/problem+json"


# --- AC-3: password rules ----------------------------------------------------------------


async def test_td001_ac3_short_password_rejected(client: httpx.AsyncClient) -> None:
    r = await client.post("/signup", json=_signup_body(password="short-pw-11"))  # 11 chars
    assert r.status_code == 422
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["title"] == "Weak password"


@pytest.mark.parametrize("password", ["Password1234", "CorrectHorseBatteryStaple", "QWERTY123456"])
async def test_td001_ac3_common_password_rejected(client: httpx.AsyncClient, password: str) -> None:
    r = await client.post("/signup", json=_signup_body(password=password))
    assert r.status_code == 422
    assert "too common" in r.json()["detail"]


async def test_td001_ac3_rejected_signup_leaves_no_tenant(client: httpx.AsyncClient) -> None:
    body = _signup_body(password="password1234")
    r = await client.post("/signup", json=body)
    assert r.status_code == 422
    assert await _tenant_id(body["slug"]) is None
