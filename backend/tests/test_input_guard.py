"""NUL characters are rejected at the boundary (M6 contract fuzzing found a 500)."""

import httpx

from tests.features.helpers import auth, tenant


async def test_nul_in_json_body_is_422_not_500(client: httpx.AsyncClient) -> None:
    r = await client.post(
        "/signup",
        content=b'{"company_name": "A\u0000B", "slug": "nul-test", "admin_name": "Ada",'
        b' "email": "a@example.com", "password": "a-long-unique-passphrase"}',
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 422
    assert r.json()["title"] == "Invalid characters"


async def test_nul_in_ticket_body_and_query_is_rejected(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    r = await client.post(f"/t/{slug}/tickets", headers=admin, json={"subject": "x", "body": "a\x00b"})
    assert r.status_code == 422
    q = await client.get(f"/t/{slug}/tickets?cursor=a%00b", headers=admin)
    assert q.status_code == 422


async def test_normal_requests_pass_through(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)  # signup body read by the guard, replayed to the app
    admin = await auth(client, slug)
    r = await client.get(f"/t/{slug}/tickets", headers=admin)
    assert r.status_code == 200
