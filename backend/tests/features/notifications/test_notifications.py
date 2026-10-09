"""TD-006 acceptance tests (PR D): in-app notifications API, assignment hook, retention."""

import base64
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.db import tenant_session
from app.features.notifications import service
from tests.features.helpers import auth, customer, staff, tenant


def _claims(headers: dict[str, str]) -> tuple[uuid.UUID, uuid.UUID]:
    """(tenant id, user id) from an access token; tests only, so no signature check."""
    payload = headers["Authorization"].split()[1].split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    return uuid.UUID(claims["tid"]), uuid.UUID(claims["sub"])


async def _push(headers: dict[str, str], key: str) -> None:
    tid, uid = _claims(headers)
    async with tenant_session(tid) as s:
        await service.notify(s, tid, [uid], "test", None, {"n": key}, key)


async def _inbox(client: httpx.AsyncClient, slug: str, who: dict[str, str]) -> dict[str, Any]:
    r = await client.get(f"/t/{slug}/notifications", headers=who)
    assert r.status_code == 200, r.text
    body: dict[str, Any] = r.json()
    return body


async def test_td006_ac5_assignment_notifies_assignee(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    sam_id, sam = await staff(client, slug, admin)
    _, cara = await customer(client, slug)
    t = (
        await client.post(f"/t/{slug}/tickets", headers=cara, json={"subject": "Help", "body": "Pls"})
    ).json()
    r = await client.patch(f"/t/{slug}/tickets/{t['number']}", headers=admin, json={"assignee_id": sam_id})
    assert r.status_code == 200
    box = await _inbox(client, slug, sam)
    assert box["unread_count"] == 1
    [n] = box["items"]
    assert n["kind"] == "ticket_assigned"
    assert n["ticket_id"] == t["id"]
    assert n["payload"] == {"number": t["number"], "subject": "Help"}  # no message content
    assert (await _inbox(client, slug, admin))["unread_count"] == 0


async def test_td006_ac5_self_assignment_does_not_notify(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    sam_id, sam = await staff(client, slug, admin)
    _, cara = await customer(client, slug)
    t = (await client.post(f"/t/{slug}/tickets", headers=cara, json={"subject": "Hi", "body": "?"})).json()
    await client.patch(f"/t/{slug}/tickets/{t['number']}", headers=sam, json={"assignee_id": sam_id})
    assert (await _inbox(client, slug, sam))["unread_count"] == 0


async def test_td006_ac1_notify_ignores_duplicate_dedupe_key(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    await _push(admin, "breach:x:first_response")
    await _push(admin, "breach:x:first_response")
    await _push(admin, "breach:x:resolution")
    assert (await _inbox(client, slug, admin))["unread_count"] == 2


async def test_td006_ac2_newest_first_max_50(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    for i in range(52):
        await _push(admin, f"k{i}")
    box = await _inbox(client, slug, admin)
    assert len(box["items"]) == 50
    assert box["unread_count"] == 52
    assert box["items"][0]["payload"] == {"n": "k51"}


async def test_td006_ac3_mark_one_and_all_read_only_own(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    _, sam = await staff(client, slug, admin)
    for k in ("a", "b"):
        await _push(admin, k)
        await _push(sam, k)
    mine = (await _inbox(client, slug, admin))["items"]
    theirs = (await _inbox(client, slug, sam))["items"]

    r = await client.post(f"/t/{slug}/notifications/{mine[0]['id']}/read", headers=admin)
    assert r.status_code == 204
    assert (await _inbox(client, slug, admin))["unread_count"] == 1
    other = await client.post(f"/t/{slug}/notifications/{theirs[0]['id']}/read", headers=admin)
    assert other.status_code == 404  # another user's notification looks like none
    assert (await client.post(f"/t/{slug}/notifications/read-all", headers=admin)).status_code == 204
    assert (await _inbox(client, slug, admin))["unread_count"] == 0
    assert (await _inbox(client, slug, sam))["unread_count"] == 2  # untouched


async def test_td006_ac6_cross_tenant_notifications_invisible(client: httpx.AsyncClient) -> None:
    a = await tenant(client)
    ada = await auth(client, a)
    await _push(ada, "secret")
    b = await tenant(client, "bob@example.com")
    bob = await auth(client, b, "bob@example.com")
    note = (await _inbox(client, a, ada))["items"][0]
    assert (await client.get(f"/t/{a}/notifications", headers=bob)).status_code == 404
    assert (await client.post(f"/t/{b}/notifications/{note['id']}/read", headers=bob)).status_code == 404
    assert (await _inbox(client, b, bob))["items"] == []
    assert (await _inbox(client, a, ada))["unread_count"] == 1


async def test_td006_ac7_notifications_older_than_90_days_are_deleted(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    await _push(admin, "old")
    tid, _ = _claims(admin)
    now = datetime.now(UTC)
    assert await service.purge_expired(tid, now + timedelta(days=89)) == 0
    assert await service.purge_expired(tid, now + timedelta(days=91)) == 1
    assert (await _inbox(client, slug, admin))["items"] == []
