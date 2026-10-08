"""TD-003 / TD-004 acceptance tests for PR C: tickets, queue, replies, notes, workflow, audit.

Written BEFORE the implementation (acceptance-tdd). API-level only, except where the
database is read to prove an audit entry exists.
"""

import uuid

import httpx
import pytest
from sqlalchemy import text

from app.core.db import system_session, tenant_session
from tests.features.helpers import auth, customer, staff, tenant


async def _setup(
    client: httpx.AsyncClient,
) -> tuple[str, dict[str, str], str, dict[str, str], str, dict[str, str]]:
    """Tenant with an admin, a staff member and a customer."""
    slug = await tenant(client)
    admin = await auth(client, slug)
    staff_id, sam = await staff(client, slug, admin)
    cust_id, cara = await customer(client, slug)
    return slug, admin, staff_id, sam, cust_id, cara


async def _open(client: httpx.AsyncClient, slug: str, who: dict[str, str], **body: object) -> httpx.Response:
    payload: dict[str, object] = {"subject": "Printer on fire", "body": "Please help."}
    payload.update(body)
    return await client.post(f"/t/{slug}/tickets", json=payload, headers=who)


# --- TD-003: create -----------------------------------------------------------------------------


async def test_td003_ac1_customer_creates_ticket_with_defaults(client: httpx.AsyncClient) -> None:
    slug, *_, cust_id, cara = await _setup(client)
    first = (await _open(client, slug, cara)).json()
    second = await _open(client, slug, cara)
    assert second.status_code == 201
    t = second.json()
    assert (first["number"], t["number"]) == (1, 2)  # per-tenant sequence
    assert t["status"] == "new" and t["priority"] == "P3" and t["category"] is None
    assert t["requester_id"] == cust_id and t["assignee_id"] is None


@pytest.mark.parametrize(("subject", "body"), [("", "x"), ("x" * 201, "x"), ("x", ""), ("x", "y" * 10_001)])
async def test_td003_ac1_length_limits(client: httpx.AsyncClient, subject: str, body: str) -> None:
    slug, *_, cara = await _setup(client)
    assert (await _open(client, slug, cara, subject=subject, body=body)).status_code == 422


async def test_td003_ac2_staff_creates_on_behalf_with_priority_and_category(
    client: httpx.AsyncClient,
) -> None:
    slug, _, _, sam, cust_id, _ = await _setup(client)
    r = await _open(client, slug, sam, requester_id=cust_id, priority="P1", category="technical")
    assert r.status_code == 201
    assert (r.json()["priority"], r.json()["category"], r.json()["requester_id"]) == (
        "P1",
        "technical",
        cust_id,
    )


async def test_td003_ac2_staff_must_name_a_customer_of_this_tenant(client: httpx.AsyncClient) -> None:
    slug, _, staff_id, sam, _, _ = await _setup(client)
    assert (await _open(client, slug, sam)).status_code == 422  # requester missing
    assert (await _open(client, slug, sam, requester_id=staff_id)).status_code == 422  # not a customer
    assert (await _open(client, slug, sam, requester_id=str(uuid.uuid4()))).status_code == 422


@pytest.mark.parametrize("field", [{"priority": "P1"}, {"category": "billing"}])
async def test_td003_ac3_customers_cannot_set_priority_or_category(
    client: httpx.AsyncClient, field: dict[str, str]
) -> None:
    slug, *_, cara = await _setup(client)
    r = await _open(client, slug, cara, **field)
    assert r.status_code == 422 and r.headers["content-type"] == "application/problem+json"


# --- TD-003: queue and view -----------------------------------------------------------------------


async def test_td003_ac4_queue_newest_first_with_filters(client: httpx.AsyncClient) -> None:
    slug, _, staff_id, sam, cust_id, cara = await _setup(client)
    for i in range(3):
        await _open(client, slug, cara, subject=f"T{i}")
    p1 = (await _open(client, slug, sam, requester_id=cust_id, priority="P1")).json()["number"]
    await client.patch(f"/t/{slug}/tickets/{p1}", json={"assignee_id": staff_id}, headers=sam)

    queue = (await client.get(f"/t/{slug}/tickets", headers=sam)).json()
    assert [t["number"] for t in queue["items"]] == [4, 3, 2, 1]
    by_prio = (await client.get(f"/t/{slug}/tickets", params={"priority": "P1"}, headers=sam)).json()
    assert [t["number"] for t in by_prio["items"]] == [p1]
    mine = (await client.get(f"/t/{slug}/tickets", params={"assignee_id": staff_id}, headers=sam)).json()
    assert [t["number"] for t in mine["items"]] == [p1]
    by_status = (await client.get(f"/t/{slug}/tickets", params={"status": "open"}, headers=sam)).json()
    assert [t["number"] for t in by_status["items"]] == [p1]  # assigning moved it new -> open


async def test_td003_ac4_cursor_pagination_and_max_page(client: httpx.AsyncClient) -> None:
    slug, *_, sam, _, cara = await _setup(client)
    for i in range(5):
        await _open(client, slug, cara, subject=f"T{i}")
    page1 = (await client.get(f"/t/{slug}/tickets", params={"limit": 2}, headers=sam)).json()
    page2 = (
        await client.get(
            f"/t/{slug}/tickets", params={"limit": 2, "cursor": page1["next_cursor"]}, headers=sam
        )
    ).json()
    page3 = (
        await client.get(
            f"/t/{slug}/tickets", params={"limit": 2, "cursor": page2["next_cursor"]}, headers=sam
        )
    ).json()
    numbers = [t["number"] for p in (page1, page2, page3) for t in p["items"]]
    assert numbers == [5, 4, 3, 2, 1] and page3["next_cursor"] is None
    assert (await client.get(f"/t/{slug}/tickets", params={"limit": 101}, headers=sam)).status_code == 422
    assert (
        await client.get(f"/t/{slug}/tickets", params={"cursor": "garbage"}, headers=sam)
    ).status_code == 422


async def test_td003_ac5_customers_see_only_their_own_tickets(client: httpx.AsyncClient) -> None:
    slug, *_, cara = await _setup(client)
    _, dan = await customer(client, slug, "dan@example.com")
    await _open(client, slug, cara, subject="Cara's")
    await _open(client, slug, dan, subject="Dan's")
    items = (await client.get(f"/t/{slug}/tickets", headers=cara)).json()["items"]
    assert [t["subject"] for t in items] == ["Cara's"]


async def test_td003_ac6_customer_cannot_view_another_customers_ticket(client: httpx.AsyncClient) -> None:
    slug, *_, cara = await _setup(client)
    _, dan = await customer(client, slug, "dan@example.com")
    number = (await _open(client, slug, dan)).json()["number"]
    assert (await client.get(f"/t/{slug}/tickets/{number}", headers=cara)).status_code == 404
    assert (await client.get(f"/t/{slug}/tickets/{number}", headers=dan)).status_code == 200


async def test_td003_ac8_other_tenants_tickets_never_visible(client: httpx.AsyncClient) -> None:
    slug_a, _, _, sam_a, _, cara_a = await _setup(client)
    slug_b = await tenant(client)
    admin_b = await auth(client, slug_b)
    await _open(client, slug_a, cara_a)
    assert (await client.get(f"/t/{slug_b}/tickets", headers=admin_b)).json()["items"] == []
    assert (await client.get(f"/t/{slug_b}/tickets/1", headers=admin_b)).status_code == 404
    assert (await client.get(f"/t/{slug_b}/tickets", headers=sam_a)).status_code == 404  # wrong-tenant token


# --- TD-004: workflow ----------------------------------------------------------------------------


async def test_td004_ac1_assign_to_staff_only_in_same_tenant(client: httpx.AsyncClient) -> None:
    slug, _, staff_id, sam, cust_id, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    ok = await client.patch(f"/t/{slug}/tickets/{n}", json={"assignee_id": staff_id}, headers=sam)
    assert ok.status_code == 200 and ok.json()["assignee_id"] == staff_id and ok.json()["status"] == "open"
    assert (
        await client.patch(f"/t/{slug}/tickets/{n}", json={"assignee_id": cust_id}, headers=sam)
    ).status_code == 422
    slug_b = await tenant(client)
    other_staff, _ = await staff(client, slug_b, await auth(client, slug_b), "zed@example.com")
    r = await client.patch(f"/t/{slug}/tickets/{n}", json={"assignee_id": other_staff}, headers=sam)
    assert r.status_code == 422


async def test_td004_customers_cannot_change_tickets(client: httpx.AsyncClient) -> None:
    slug, *_, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    assert (
        await client.patch(f"/t/{slug}/tickets/{n}", json={"status": "resolved"}, headers=cara)
    ).status_code == 403


async def test_td004_ac2_first_staff_reply_sets_first_replied_at(client: httpx.AsyncClient) -> None:
    slug, *_, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    r = await client.post(f"/t/{slug}/tickets/{n}/messages", json={"body": "On it."}, headers=sam)
    assert r.status_code == 201
    t = (await client.get(f"/t/{slug}/tickets/{n}", headers=cara)).json()
    first = t["first_replied_at"]
    assert first is not None and t["status"] == "open"
    await client.post(f"/t/{slug}/tickets/{n}/messages", json={"body": "Still on it."}, headers=sam)
    assert (await client.get(f"/t/{slug}/tickets/{n}", headers=cara)).json()["first_replied_at"] == first


async def test_td004_ac3_internal_notes_never_reach_customers(client: httpx.AsyncClient) -> None:
    slug, *_, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    await client.post(
        f"/t/{slug}/tickets/{n}/messages", json={"body": "secret note", "internal": True}, headers=sam
    )
    await client.post(f"/t/{slug}/tickets/{n}/messages", json={"body": "public reply"}, headers=sam)
    as_customer = (await client.get(f"/t/{slug}/tickets/{n}", headers=cara)).json()
    as_staff = (await client.get(f"/t/{slug}/tickets/{n}", headers=sam)).json()
    assert [m["body"] for m in as_customer["messages"]] == ["Please help.", "public reply"]
    assert "secret note" in [m["body"] for m in as_staff["messages"]]
    # an internal note is not a "first reply"
    assert as_customer["first_replied_at"] is not None  # set by the public reply, not the note


async def test_td004_ac3_customers_cannot_post_internal_notes(client: httpx.AsyncClient) -> None:
    slug, *_, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    r = await client.post(
        f"/t/{slug}/tickets/{n}/messages", json={"body": "x", "internal": True}, headers=cara
    )
    assert r.status_code == 403


@pytest.mark.parametrize("start", ["pending_customer", "resolved"])
async def test_td004_ac4_customer_reply_reopens(client: httpx.AsyncClient, start: str) -> None:
    slug, *_, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    await client.patch(f"/t/{slug}/tickets/{n}", json={"status": "open"}, headers=sam)
    assert (
        await client.patch(f"/t/{slug}/tickets/{n}", json={"status": start}, headers=sam)
    ).status_code == 200
    await client.post(f"/t/{slug}/tickets/{n}/messages", json={"body": "Any news?"}, headers=cara)
    assert (await client.get(f"/t/{slug}/tickets/{n}", headers=cara)).json()["status"] == "open"


async def test_td004_customer_cannot_reply_to_someone_elses_ticket(client: httpx.AsyncClient) -> None:
    slug, *_, cara = await _setup(client)
    _, dan = await customer(client, slug, "dan@example.com")
    n = (await _open(client, slug, dan)).json()["number"]
    assert (
        await client.post(f"/t/{slug}/tickets/{n}/messages", json={"body": "hi"}, headers=cara)
    ).status_code == 404


@pytest.mark.parametrize(
    ("path", "target"),
    [(["new"], "pending_customer"), (["new", "open", "resolved"], "pending_customer")],
)
async def test_td004_ac5_illegal_transitions_are_409(
    client: httpx.AsyncClient, path: list[str], target: str
) -> None:
    slug, *_, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    for step in path[1:]:
        assert (
            await client.patch(f"/t/{slug}/tickets/{n}", json={"status": step}, headers=sam)
        ).status_code == 200
    r = await client.patch(f"/t/{slug}/tickets/{n}", json={"status": target}, headers=sam)
    assert r.status_code == 409 and r.headers["content-type"] == "application/problem+json"


async def test_td004_ac6_changes_are_audited(client: httpx.AsyncClient) -> None:
    slug, _, staff_id, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    r = await client.patch(
        f"/t/{slug}/tickets/{n}",
        json={"assignee_id": staff_id, "priority": "P2", "category": "billing"},
        headers=sam,
    )
    assert r.status_code == 200
    async with system_session() as s:
        tid = (await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug})).scalar_one()
    async with tenant_session(uuid.UUID(str(tid))) as s:
        rows = (
            await s.execute(
                text("SELECT action, actor_id, data FROM audit_log WHERE entity = 'ticket' ORDER BY action")
            )
        ).all()
    changes = {r.action: r.data for r in rows}
    assert changes["ticket.assignee_changed"] == {"from": None, "to": staff_id}
    assert changes["ticket.priority_changed"] == {"from": "P3", "to": "P2"}
    assert changes["ticket.category_changed"] == {"from": None, "to": "billing"}
    assert changes["ticket.status_changed"] == {"from": "new", "to": "open"}
    assert {str(r.actor_id) for r in rows} == {staff_id}


async def test_td004_ac8_no_writes_to_another_tenants_ticket(client: httpx.AsyncClient) -> None:
    slug_a, *_, cara_a = await _setup(client)
    await _open(client, slug_a, cara_a)
    slug_b, _, _, sam_b, _, _ = await _setup(client)
    assert (
        await client.post(f"/t/{slug_b}/tickets/1/messages", json={"body": "x"}, headers=sam_b)
    ).status_code == 404
    assert (
        await client.patch(f"/t/{slug_b}/tickets/1", json={"status": "open"}, headers=sam_b)
    ).status_code == 404
    async with system_session() as s:
        tid = (await s.execute(text("SELECT resolve_tenant_slug(:s)"), {"s": slug_a})).scalar_one()
    async with tenant_session(uuid.UUID(str(tid))) as s:
        assert (await s.execute(text("SELECT status FROM tickets"))).scalar_one() == "new"  # untouched


async def test_td004_assign_and_open_in_one_request(client: httpx.AsyncClient) -> None:
    """Code review: assignment already moves new -> open; asking for open too must not 409."""
    slug, _, staff_id, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    r = await client.patch(
        f"/t/{slug}/tickets/{n}", json={"assignee_id": staff_id, "status": "open"}, headers=sam
    )
    assert r.status_code == 200 and r.json()["status"] == "open"


async def test_td004_same_status_is_a_noop(client: httpx.AsyncClient) -> None:
    slug, *_, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    r = await client.patch(f"/t/{slug}/tickets/{n}", json={"status": "new"}, headers=sam)
    assert r.status_code == 200 and r.json()["status"] == "new"


@pytest.mark.parametrize("field", ["status", "priority"])
async def test_td004_null_status_or_priority_is_422(client: httpx.AsyncClient, field: str) -> None:
    slug, *_, sam, _, cara = await _setup(client)
    n = (await _open(client, slug, cara)).json()["number"]
    assert (await client.patch(f"/t/{slug}/tickets/{n}", json={field: None}, headers=sam)).status_code == 422


async def test_td003_ac4_naive_cursor_is_422_not_500(client: httpx.AsyncClient) -> None:
    import base64

    slug, *_, sam, _, _ = await _setup(client)
    naive = base64.urlsafe_b64encode(b"2026-10-08T10:00:00|5").decode()
    assert (await client.get(f"/t/{slug}/tickets", params={"cursor": naive}, headers=sam)).status_code == 422
