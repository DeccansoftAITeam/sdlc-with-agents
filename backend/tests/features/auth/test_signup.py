"""TD-001 acceptance tests for T-001-02: signup, slug and password rules, verification.

Written BEFORE the implementation (acceptance-tdd). They talk to the API only, the way a
browser would, and inspect the database only to prove secrets are stored hashed.
"""

import re
import uuid
from typing import Any

import httpx
import pytest
from sqlalchemy import text

from app.core.db import system_session, tenant_session
from app.core.email import InMemoryOutbox

PASSWORD = "a-long-unique-passphrase"
LINK = re.compile(r"/t/(?P<slug>[a-z0-9-]+)/verify\?token=(?P<token>[A-Za-z0-9_-]+)")


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


async def _tenant_id(slug: str) -> uuid.UUID:
    async with system_session() as s:
        tid = (await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one()
    assert tid is not None
    return uuid.UUID(str(tid))


def _token_from(outbox: InMemoryOutbox) -> tuple[str, str]:
    m = LINK.search(outbox.messages[-1].body)
    assert m, "verification email must contain /t/<slug>/verify?token=<token>"
    return m["slug"], m["token"]


# --- AC-1: signup creates the tenant + first admin and sends a verification email --------


async def test_td001_ac1_signup_creates_tenant_admin_and_sends_verification(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    body = _signup_body()
    r = await client.post("/signup", json=body)
    assert r.status_code == 201
    assert r.json() == {"tenant_slug": body["slug"]}

    tid = await _tenant_id(body["slug"])
    async with tenant_session(tid) as s:
        row = (await s.execute(text("SELECT email, role, email_verified_at, password_hash FROM users"))).one()
    assert row.email == "ada@example.com"  # normalised
    assert row.role == "admin"
    assert row.email_verified_at is None
    assert row.password_hash.startswith("$argon2id$")  # ADR-0002

    assert len(outbox.messages) == 1
    assert outbox.messages[0].to == "ada@example.com"
    slug, _ = _token_from(outbox)
    assert slug == body["slug"]


async def test_td001_ac1_verification_token_is_stored_hashed(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    body = _signup_body()
    await client.post("/signup", json=body)
    _, token = _token_from(outbox)
    async with tenant_session(await _tenant_id(body["slug"])) as s:
        hashes = (await s.execute(text("SELECT token_hash FROM email_tokens"))).scalars().all()
    assert len(hashes) == 1 and token not in hashes[0] and len(hashes[0]) == 64


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


@pytest.mark.parametrize("slug", ["ab", "Has-Caps", "under_score", "x" * 41, "spa ce"])
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


async def test_td001_ac3_breached_password_rejected(client: httpx.AsyncClient) -> None:
    r = await client.post("/signup", json=_signup_body(password="CorrectHorseBatteryStaple"))
    assert r.status_code == 422
    assert "breach" in r.json()["detail"].lower()


async def test_td001_ac3_rejected_signup_leaves_no_tenant(client: httpx.AsyncClient) -> None:
    body = _signup_body(password="password1234")
    r = await client.post("/signup", json=body)
    assert r.status_code == 422
    async with system_session() as s:
        assert (
            await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": body["slug"]})
        ).scalar_one() is None


# --- AC-9: verification links -----------------------------------------------------------


async def test_td001_ac9_valid_link_marks_email_verified(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    body = _signup_body()
    await client.post("/signup", json=body)
    slug, token = _token_from(outbox)
    r = await client.post(f"/t/{slug}/auth/verify", json={"token": token})
    assert r.status_code == 204
    async with tenant_session(await _tenant_id(slug)) as s:
        verified = (await s.execute(text("SELECT email_verified_at FROM users"))).scalar_one()
    assert verified is not None


async def test_td001_ac9_link_is_single_use(client: httpx.AsyncClient, outbox: InMemoryOutbox) -> None:
    await client.post("/signup", json=_signup_body())
    slug, token = _token_from(outbox)
    assert (await client.post(f"/t/{slug}/auth/verify", json={"token": token})).status_code == 204
    r = await client.post(f"/t/{slug}/auth/verify", json={"token": token})
    assert r.status_code == 400
    assert r.headers["content-type"] == "application/problem+json"


async def test_td001_ac9_link_expires_after_30_minutes(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    await client.post("/signup", json=_signup_body())
    slug, token = _token_from(outbox)
    async with tenant_session(await _tenant_id(slug)) as s:
        expiry = (await s.execute(text("SELECT expires_at - created_at FROM email_tokens"))).scalar_one()
        assert expiry.total_seconds() == 30 * 60
        await s.execute(
            text(
                "UPDATE email_tokens SET created_at = now() - interval '31 minutes', "
                "expires_at = now() - interval '1 minute'"
            )
        )
    r = await client.post(f"/t/{slug}/auth/verify", json={"token": token})
    assert r.status_code == 400


async def test_td001_ac9_link_from_another_tenant_rejected(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    """Cross-tenant: a token minted for tenant A means nothing under tenant B's slug."""
    await client.post("/signup", json=_signup_body())
    _, token_a = _token_from(outbox)
    body_b = _signup_body()
    await client.post("/signup", json=body_b)
    r = await client.post(f"/t/{body_b['slug']}/auth/verify", json={"token": token_a})
    assert r.status_code == 400


async def test_td001_ac9_unknown_tenant_slug_is_404(client: httpx.AsyncClient) -> None:
    r = await client.post("/t/no-such-tenant/auth/verify", json={"token": "x" * 43})
    assert r.status_code == 404


async def test_td001_ac9_resend_invalidates_the_previous_link(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    body = _signup_body()
    await client.post("/signup", json=body)
    slug, old = _token_from(outbox)
    r = await client.post(f"/t/{slug}/auth/verify/resend", json={"email": body["email"]})
    assert r.status_code == 202
    _, new = _token_from(outbox)
    assert new != old
    assert (await client.post(f"/t/{slug}/auth/verify", json={"token": old})).status_code == 400
    assert (await client.post(f"/t/{slug}/auth/verify", json={"token": new})).status_code == 204


# --- AC-7: no account enumeration on resend ----------------------------------------------


async def test_td001_ac7_resend_response_identical_for_unknown_email(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    body = _signup_body()
    await client.post("/signup", json=body)
    slug = body["slug"]
    known = await client.post(f"/t/{slug}/auth/verify/resend", json={"email": body["email"]})
    unknown = await client.post(f"/t/{slug}/auth/verify/resend", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert all(m.to != "nobody@example.com" for m in outbox.messages)


async def test_td001_ac9_concurrent_resends_never_fail(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    """Review finding: racing resends must serialise, not 500 on the one-live-token index."""
    import asyncio

    body = _signup_body()
    await client.post("/signup", json=body)
    url = f"/t/{body['slug']}/auth/verify/resend"
    results = await asyncio.gather(*(client.post(url, json={"email": body["email"]}) for _ in range(5)))
    assert {r.status_code for r in results} == {202}
    _, latest = _token_from(outbox)
    assert (await client.post(f"/t/{body['slug']}/auth/verify", json={"token": latest})).status_code == 204


async def test_td001_ac9_deactivated_user_cannot_verify(
    client: httpx.AsyncClient, outbox: InMemoryOutbox
) -> None:
    """Security review #5: a live link must not verify a deactivated account."""
    body = _signup_body()
    await client.post("/signup", json=body)
    slug, token = _token_from(outbox)
    async with tenant_session(await _tenant_id(slug)) as s:
        await s.execute(text("UPDATE users SET is_active = false"))
    assert (await client.post(f"/t/{slug}/auth/verify", json={"token": token})).status_code == 400
    async with tenant_session(await _tenant_id(slug)) as s:
        assert (await s.execute(text("SELECT email_verified_at FROM users"))).scalar_one() is None
