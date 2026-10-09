"""Shared API-level helpers for feature tests: create a tenant, accounts, and log in."""

import uuid

import httpx

PASSWORD = "a-long-unique-passphrase"
USER_PASSWORD = "another-long-passphrase"


async def tenant(client: httpx.AsyncClient, admin_email: str = "ada@example.com") -> str:
    slug = f"acme-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/signup",
        json={
            "company_name": "Acme",
            "slug": slug,
            "admin_name": "Ada",
            "email": admin_email,
            "password": PASSWORD,
        },
    )
    assert r.status_code == 201, r.text
    return slug


async def auth(
    client: httpx.AsyncClient, slug: str, email: str = "ada@example.com", password: str = PASSWORD
) -> dict[str, str]:
    r = await client.post(f"/t/{slug}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def staff(
    client: httpx.AsyncClient,
    slug: str,
    admin: dict[str, str],
    email: str = "sam@example.com",
    role: str = "staff",
) -> tuple[str, dict[str, str]]:
    """Create a staff/admin account; return (user id, auth headers)."""
    r = await client.post(
        f"/t/{slug}/users",
        headers=admin,
        json={"name": email.split("@")[0], "email": email, "password": USER_PASSWORD, "role": role},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"], await auth(client, slug, email, USER_PASSWORD)


async def customer(
    client: httpx.AsyncClient, slug: str, email: str = "cara@example.com"
) -> tuple[str, dict[str, str]]:
    r = await client.post(
        f"/t/{slug}/auth/register",
        json={"name": email.split("@")[0], "email": email, "password": USER_PASSWORD},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"], await auth(client, slug, email, USER_PASSWORD)


def claims(headers: dict[str, str]) -> tuple[uuid.UUID, uuid.UUID]:
    """(tenant id, user id) from an access token; tests only, so no signature check."""
    import base64
    import json

    payload = headers["Authorization"].split()[1].split(".")[1]
    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    return uuid.UUID(data["tid"]), uuid.UUID(data["sub"])
