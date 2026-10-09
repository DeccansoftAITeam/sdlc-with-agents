"""TD-005 acceptance tests (PR D): SLA settings API and stored ticket deadlines."""

from datetime import datetime, timedelta
from typing import Any

import httpx

from tests.features.helpers import auth, customer, staff, tenant

TARGETS: dict[str, Any] = {
    "P1": {"first_response_minutes": 30, "resolution_minutes": 120},
    "P2": {"first_response_minutes": 240, "resolution_minutes": 540},
    "P3": {"first_response_minutes": 540, "resolution_minutes": 1620},
    "P4": {"first_response_minutes": 1620, "resolution_minutes": 5400},
}
POLICY: dict[str, Any] = {
    "targets": TARGETS,
    "timezone": "Asia/Kolkata",
    "schedule": {"days": [0, 1, 2, 3, 4, 5], "start": "08:00:00", "end": "20:00:00"},
}


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


async def _p1(client: httpx.AsyncClient, slug: str, sam: dict[str, str], cust_id: str) -> dict[str, Any]:
    r = await client.post(
        f"/t/{slug}/tickets",
        headers=sam,
        json={"subject": "Down", "body": "All down.", "priority": "P1", "requester_id": cust_id},
    )
    assert r.status_code == 201, r.text
    body: dict[str, Any] = r.json()
    return body


async def test_td005_ac1_new_tenant_has_default_policy(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    r = await client.get(f"/t/{slug}/sla-settings", headers=await auth(client, slug))
    assert r.status_code == 200
    body = r.json()
    assert body["timezone"] == "UTC"
    assert body["schedule"] == {"days": [0, 1, 2, 3, 4], "start": "09:00:00", "end": "18:00:00"}
    assert body["targets"]["P1"] == {"first_response_minutes": 60, "resolution_minutes": 480}
    assert body["targets"]["P4"] == {"first_response_minutes": 1620, "resolution_minutes": 5400}


async def test_td005_ac2_admin_updates_policy(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    r = await client.put(f"/t/{slug}/sla-settings", headers=admin, json=POLICY)
    assert r.status_code == 200, r.text
    assert (await client.get(f"/t/{slug}/sla-settings", headers=admin)).json() == POLICY


async def test_td005_ac2_only_admins_see_or_change_policy(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    _, sam = await staff(client, slug, admin)
    assert (await client.get(f"/t/{slug}/sla-settings", headers=sam)).status_code == 403
    assert (await client.put(f"/t/{slug}/sla-settings", headers=sam, json=POLICY)).status_code == 403


async def test_td005_ac2_rejects_invalid_policies(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    week = {"start": "09:00:00", "end": "18:00:00"}
    bad = [
        {**POLICY, "timezone": "Mars/Olympus"},
        {**POLICY, "schedule": {"days": [0], "start": "18:00:00", "end": "09:00:00"}},
        {**POLICY, "schedule": {"days": [0, 7], **week}},
        {**POLICY, "schedule": {"days": [], **week}},
        {**POLICY, "targets": {k: v for k, v in TARGETS.items() if k != "P4"}},
        {**POLICY, "targets": {**TARGETS, "P2": {"first_response_minutes": 600, "resolution_minutes": 60}}},
        {**POLICY, "targets": {**TARGETS, "P2": {"first_response_minutes": 0, "resolution_minutes": 60}}},
        {  # 1 h a week can never reach a 60-day target: would make every new P4 ticket a 500
            **POLICY,
            "schedule": {"days": [0], "start": "09:00:00", "end": "10:00:00"},
            "targets": {**TARGETS, "P4": {"first_response_minutes": 60, "resolution_minutes": 86400}},
        },
    ]
    for policy in bad:
        r = await client.put(f"/t/{slug}/sla-settings", headers=admin, json=policy)
        assert r.status_code == 422, policy


async def test_td005_ac2_policy_change_applies_to_new_tickets_only(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    _, sam = await staff(client, slug, admin)
    cust_id, _ = await customer(client, slug)
    before = await _p1(client, slug, sam, cust_id)
    await client.put(f"/t/{slug}/sla-settings", headers=admin, json=POLICY)  # P1 first response 60 -> 30
    after = await _p1(client, slug, sam, cust_id)

    old = (await client.get(f"/t/{slug}/tickets/{before['number']}", headers=sam)).json()
    assert ts(old["first_response_due_at"]) - ts(old["created_at"]) == timedelta(minutes=60)
    assert ts(after["first_response_due_at"]) - ts(after["created_at"]) == timedelta(minutes=30)


async def test_td005_ac7_deadlines_stored_on_create(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    _, sam = await staff(client, slug, admin)
    cust_id, cara = await customer(client, slug)
    t = await _p1(client, slug, sam, cust_id)
    assert ts(t["first_response_due_at"]) - ts(t["created_at"]) == timedelta(hours=1)
    assert ts(t["resolution_due_at"]) - ts(t["created_at"]) == timedelta(hours=8)
    mine = (await client.post(f"/t/{slug}/tickets", headers=cara, json={"subject": "Hi", "body": "?"})).json()
    assert mine["first_response_due_at"] is not None  # P3, business hours


async def test_td005_ac7_priority_change_recomputes(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    _, sam = await staff(client, slug, admin)
    cust_id, _ = await customer(client, slug)
    t = await _p1(client, slug, sam, cust_id)
    r = await client.patch(f"/t/{slug}/tickets/{t['number']}", headers=sam, json={"priority": "P4"})
    assert r.status_code == 200
    assert ts(r.json()["first_response_due_at"]) > ts(t["first_response_due_at"]) + timedelta(days=1)


async def test_td005_ac5_ac7_pending_customer_pauses_resolution(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    _, sam = await staff(client, slug, admin)
    cust_id, cara = await customer(client, slug)
    t = await _p1(client, slug, sam, cust_id)
    url = f"/t/{slug}/tickets/{t['number']}"
    await client.patch(url, headers=sam, json={"status": "open"})
    paused = (await client.patch(url, headers=sam, json={"status": "pending_customer"})).json()
    assert paused["resolution_due_at"] is None  # clock stopped
    assert paused["first_response_due_at"] == t["first_response_due_at"]  # never paused

    await client.post(f"{url}/messages", headers=cara, json={"body": "Here you go."})
    resumed = (await client.get(url, headers=sam)).json()
    assert resumed["status"] == "open"
    assert ts(resumed["resolution_due_at"]) > ts(t["resolution_due_at"])  # pushed back by the pause
    assert ts(resumed["resolution_due_at"]) - ts(t["resolution_due_at"]) < timedelta(minutes=1)


async def test_td005_cross_tenant_policy_is_invisible(client: httpx.AsyncClient) -> None:
    a = await tenant(client)
    b = await tenant(client, "bob@example.com")
    bob = await auth(client, b, "bob@example.com")
    assert (await client.get(f"/t/{a}/sla-settings", headers=bob)).status_code == 404
    assert (await client.put(f"/t/{a}/sla-settings", headers=bob, json=POLICY)).status_code == 404


async def test_td005_ac7_reopen_recomputes_without_restarting(client: httpx.AsyncClient) -> None:
    slug = await tenant(client)
    admin = await auth(client, slug)
    _, sam = await staff(client, slug, admin)
    cust_id, cara = await customer(client, slug)
    t = await _p1(client, slug, sam, cust_id)
    url = f"/t/{slug}/tickets/{t['number']}"
    await client.patch(url, headers=sam, json={"status": "resolved"})
    await client.post(f"{url}/messages", headers=cara, json={"body": "Still broken."})
    reopened = (await client.get(url, headers=sam)).json()
    assert reopened["status"] == "open"
    assert reopened["first_response_due_at"] == t["first_response_due_at"]  # counted from creation
    assert reopened["resolution_due_at"] == t["resolution_due_at"]
