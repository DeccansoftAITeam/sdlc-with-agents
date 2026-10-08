"""TD-001 acceptance tests for T-001-03 (PR A): login, JWT, refresh rotation, rate limits.

Written BEFORE the implementation (acceptance-tdd). API-level only. The refresh cookie
is read from Set-Cookie and sent back explicitly, the way a browser would on the
cookie's path.
"""

import base64
import json
import uuid
from http.cookies import SimpleCookie
from typing import Any

import httpx
import pytest
from sqlalchemy import text

from app.core.db import system_session, tenant_session

PASSWORD = "a-long-unique-passphrase"
WRONG = "not-the-right-passphrase"  # deliberately wrong credential for negative tests


# --- helpers ------------------------------------------------------------------------------


async def _tenant(client: httpx.AsyncClient, email: str = "ada@example.com") -> str:
    slug = f"acme-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/signup",
        json={
            "company_name": "Acme",
            "slug": slug,
            "admin_name": "Ada",
            "email": email,
            "password": PASSWORD,
        },
    )
    assert r.status_code == 201, r.text
    return slug


async def _login(
    client: httpx.AsyncClient, slug: str, email: str = "ada@example.com", password: str = PASSWORD
) -> httpx.Response:
    return await client.post(f"/t/{slug}/auth/login", json={"email": email, "password": password})


def _refresh_cookie(r: httpx.Response) -> SimpleCookie:
    jar: SimpleCookie = SimpleCookie()
    jar.load(r.headers["set-cookie"])
    assert "refresh_token" in jar
    return jar


async def _refresh(client: httpx.AsyncClient, slug: str, token: str) -> httpx.Response:
    return await client.post(f"/t/{slug}/auth/refresh", headers={"Cookie": f"refresh_token={token}"})


def _claims(jwt: str) -> tuple[dict[str, Any], dict[str, Any]]:
    def part(seg: str) -> dict[str, Any]:
        return json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))

    head, body, _ = jwt.split(".")
    return part(head), part(body)


async def _tenant_id(slug: str) -> uuid.UUID:
    async with system_session() as s:
        return uuid.UUID(
            str((await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one())
        )


# --- AC-4: login ---------------------------------------------------------------------------


async def test_td001_ac4_login_returns_15min_eddsa_access_token(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    r = await _login(client, slug, email="ADA@example.com")  # email is case-insensitive
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["expires_in"] == 900
    header, claims = _claims(body["access_token"])
    assert header["alg"] == "EdDSA"
    assert {"sub", "tid", "role", "jti", "exp", "iat"} <= claims.keys()
    assert claims["tid"] == str(await _tenant_id(slug))
    assert claims["role"] == "admin"
    assert claims["exp"] - claims["iat"] == 900


async def test_td001_ac4_login_sets_hardened_refresh_cookie(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    cookie = _refresh_cookie(await _login(client, slug))["refresh_token"]
    assert cookie["httponly"] and cookie["secure"]
    assert cookie["samesite"].lower() == "strict"
    assert cookie["path"] == f"/api/t/{slug}/auth"
    assert int(cookie["max-age"]) == 7 * 24 * 3600


async def test_td001_ac4_refresh_token_is_stored_hashed(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    raw = _refresh_cookie(await _login(client, slug))["refresh_token"].value
    async with tenant_session(await _tenant_id(slug)) as s:
        hashes = (await s.execute(text("SELECT token_hash FROM refresh_tokens"))).scalars().all()
    assert len(hashes) == 1 and raw not in hashes[0]


async def test_td001_ac4_credentials_only_work_in_their_own_tenant(client: httpx.AsyncClient) -> None:
    """Identity is per tenant: Ada of tenant A can't log in at tenant B's address."""
    slug_a = await _tenant(client)
    slug_b = await _tenant(client, email="bob@example.com")
    assert (await _login(client, slug_b)).status_code == 401
    assert (await _login(client, slug_a)).status_code == 200


async def test_td001_ac4_unknown_tenant_is_404(client: httpx.AsyncClient) -> None:
    assert (await _login(client, "no-such-tenant")).status_code == 404


# --- AC-7: no enumeration --------------------------------------------------------------------


async def test_td001_ac7_wrong_password_and_unknown_email_look_identical(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    wrong_pw = await _login(client, slug, password=WRONG)
    unknown = await _login(client, slug, email="nobody@example.com")
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()
    assert wrong_pw.headers["content-type"] == "application/problem+json"


async def test_td001_ac7_unknown_email_still_runs_a_password_hash(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Timing proxy: we assert the unknown-email path does the same expensive work (one Argon2
    verification against a dummy hash) rather than measuring wall-clock time, which is flaky.
    An unknown *tenant slug* returns 404 before any hash; slugs are public, so that is fine."""
    from app.features.auth import sessions

    calls: list[str] = []
    real = sessions.verify_password
    monkeypatch.setattr(sessions, "verify_password", lambda h, p: calls.append(h) or real(h, p))
    slug = await _tenant(client)
    await _login(client, slug, email="nobody@example.com")
    assert len(calls) == 1 and calls[0].startswith("$argon2id$")


async def test_td001_ac7_deactivated_user_gets_the_same_401(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    async with tenant_session(await _tenant_id(slug)) as s:
        await s.execute(text("UPDATE users SET is_active = false"))
    r = await _login(client, slug)
    unknown = await _login(client, slug, email="nobody@example.com")
    assert r.status_code == 401 and r.json() == unknown.json()


# --- AC-5 / AC-6: refresh rotation and reuse detection ---------------------------------------


async def test_td001_ac5_refresh_rotates_the_pair(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    first = _refresh_cookie(await _login(client, slug))["refresh_token"].value
    r = await _refresh(client, slug, first)
    assert r.status_code == 200
    assert _claims(r.json()["access_token"])[1]["tid"] == str(await _tenant_id(slug))
    second = _refresh_cookie(r)["refresh_token"].value
    assert second != first


async def test_td001_ac6_reusing_a_refresh_token_revokes_the_whole_family(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    first = _refresh_cookie(await _login(client, slug))["refresh_token"].value
    second = _refresh_cookie(await _refresh(client, slug, first))["refresh_token"].value
    # An attacker replays the stolen first token...
    assert (await _refresh(client, slug, first)).status_code == 401
    # ...and the legitimate user's current token dies with the family (TM-001).
    assert (await _refresh(client, slug, second)).status_code == 401


async def test_td001_ac6_expired_refresh_token_rejected(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    token = _refresh_cookie(await _login(client, slug))["refresh_token"].value
    async with tenant_session(await _tenant_id(slug)) as s:
        await s.execute(
            text(
                "UPDATE refresh_tokens SET created_at = now() - interval '8 days', "
                "expires_at = now() - interval '1 day'"
            )
        )
    assert (await _refresh(client, slug, token)).status_code == 401


async def test_td001_ac6_refresh_token_from_another_tenant_rejected(client: httpx.AsyncClient) -> None:
    slug_a = await _tenant(client)
    slug_b = await _tenant(client, email="bob@example.com")
    token_a = _refresh_cookie(await _login(client, slug_a))["refresh_token"].value
    assert (await _refresh(client, slug_b, token_a)).status_code == 401


async def test_td001_ac6_missing_cookie_rejected(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    assert (await client.post(f"/t/{slug}/auth/refresh")).status_code == 401


async def test_td001_logout_revokes_the_session(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    token = _refresh_cookie(await _login(client, slug))["refresh_token"].value
    r = await client.post(f"/t/{slug}/auth/logout", headers={"Cookie": f"refresh_token={token}"})
    assert r.status_code == 204
    assert (await _refresh(client, slug, token)).status_code == 401


# --- AC-12: token tenant must match the URL ------------------------------------------------


async def test_td001_ac12_me_works_with_matching_slug(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    access = (await _login(client, slug)).json()["access_token"]
    r = await client.get(f"/t/{slug}/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ada@example.com" and r.json()["role"] == "admin"


async def test_td001_ac12_slug_mismatch_is_404(client: httpx.AsyncClient) -> None:
    slug_a = await _tenant(client)
    slug_b = await _tenant(client, email="bob@example.com")
    access_a = (await _login(client, slug_a)).json()["access_token"]
    r = await client.get(f"/t/{slug_b}/me", headers={"Authorization": f"Bearer {access_a}"})
    assert r.status_code == 404


@pytest.mark.parametrize("auth", [None, "Bearer not-a-jwt", "Basic abc"])
async def test_td001_ac12_missing_or_malformed_token_is_401(
    client: httpx.AsyncClient, auth: str | None
) -> None:
    slug = await _tenant(client)
    headers = {"Authorization": auth} if auth else {}
    assert (await client.get(f"/t/{slug}/me", headers=headers)).status_code == 401


async def test_td001_ac12_tampered_or_unsigned_token_is_401(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    access = (await _login(client, slug)).json()["access_token"]
    head, body, sig = access.split(".")
    claims = _claims(access)[1] | {"role": "admin", "sub": str(uuid.uuid4())}
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    none_head = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    for token in (f"{head}.{forged}.{sig}", f"{none_head}.{body}."):
        r = await client.get(f"/t/{slug}/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


# --- AC-8: rate limits -----------------------------------------------------------------------


async def test_td001_ac8_sixth_failed_login_for_an_email_is_429(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    for _ in range(5):
        assert (await _login(client, slug, password=WRONG)).status_code == 401
    r = await _login(client, slug, password=WRONG)
    assert r.status_code == 429
    assert r.headers["content-type"] == "application/problem+json"
    assert int(r.headers["retry-after"]) > 0
    # Locked even with the right password, for that email only...
    assert (await _login(client, slug)).status_code == 429


async def test_td001_ac8_twenty_first_login_from_one_ip_is_429(client: httpx.AsyncClient) -> None:
    slug = await _tenant(client)
    for i in range(20):
        await _login(client, slug, email=f"user{i}@example.com")
    assert (await _login(client, slug, email="another@example.com")).status_code == 429


async def test_td001_ac8_fourth_signup_from_one_ip_in_an_hour_is_429(client: httpx.AsyncClient) -> None:
    """Closes TM-013 (scripted self-serve signups)."""
    for _ in range(3):
        await _tenant(client)
    r = await client.post(
        "/signup",
        json={
            "company_name": "X",
            "slug": f"x-{uuid.uuid4().hex[:8]}",
            "admin_name": "X",
            "email": "x@example.com",
            "password": PASSWORD,
        },
    )
    assert r.status_code == 429


def test_access_token_lifetime_constant() -> None:
    from app.core.security import ACCESS_TTL_SECONDS

    assert ACCESS_TTL_SECONDS == 900


async def test_td001_ac8_failed_signups_do_not_count(client: httpx.AsyncClient) -> None:
    """Review finding: three typos must not lock a real user out of signing up for an hour."""
    for _ in range(3):
        r = await client.post(
            "/signup",
            json={
                "company_name": "X",
                "slug": f"x-{uuid.uuid4().hex[:8]}",
                "admin_name": "X",
                "email": "x@example.com",
                "password": "short",
            },
        )
        assert r.status_code == 422
    await _tenant(client)  # the real attempt still succeeds


async def test_td001_ac6_concurrent_refresh_with_same_token_revokes_family(client: httpx.AsyncClient) -> None:
    """Review finding: two refreshes racing with one token are serialised (FOR UPDATE). At most
    one succeeds; the other looks like reuse and revokes the family. Trade-off: two browser tabs
    refreshing at the same instant log the user out (recorded in the progress decisions)."""
    import asyncio

    slug = await _tenant(client)
    token = _refresh_cookie(await _login(client, slug))["refresh_token"].value
    results = await asyncio.gather(*(_refresh(client, slug, token) for _ in range(2)))
    assert sorted(r.status_code for r in results) in ([200, 401], [401, 401])
    for r in results:
        if r.status_code == 200:  # the winner's new token died with the family
            assert (
                await _refresh(client, slug, _refresh_cookie(r)["refresh_token"].value)
            ).status_code == 401


async def test_td001_bad_signing_key_config_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security finding: outside local, a missing key is a startup error, never an ephemeral key."""
    from app.core import security
    from app.core.config import get_settings

    monkeypatch.setenv("ENVIRONMENT", "staging")
    get_settings.cache_clear()
    security._signing_key.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="JWT_PRIVATE_KEY_PEM"):
            security.check_signing_key()
    finally:
        monkeypatch.delenv("ENVIRONMENT")
        get_settings.cache_clear()
        security._signing_key.cache_clear()


def test_rate_limit_buckets_are_bounded_and_pruned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security finding: unique keys must not grow memory without bound."""
    from app.core import ratelimit

    monkeypatch.setattr(ratelimit, "MAX_KEYS", 10)
    for i in range(50):
        ratelimit.hit(f"k{i}", 5, 60)
    assert len(ratelimit._buckets) <= 10
    ratelimit.forget_last("k49")
    assert "k49" not in ratelimit._buckets
