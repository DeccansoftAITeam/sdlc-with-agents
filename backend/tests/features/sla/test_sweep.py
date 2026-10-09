"""TD-007 acceptance tests (PR E): the breach sweep.

No sleeping and no fake clock: tests move a ticket's stored deadline into the past (through
the app role, under RLS) and run one sweep. The sweep itself only ever uses the DB's now().
"""

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select, text

from app.core.audit import AuditEntry
from app.core.db import tenant_session
from app.features.sla.sweep import _sweep_tenant, sweep
from tests.features.helpers import auth, claims, customer, staff, tenant

FLAG = "sla-breach-escalation"


@dataclass
class Desk:
    slug: str
    tenant_id: uuid.UUID
    admin: dict[str, str]
    admin_id: uuid.UUID
    sam_id: str
    sam: dict[str, str]
    cust_id: str
    cara: dict[str, str]


async def _desk(client: httpx.AsyncClient, *, flag: bool = True, email: str = "ada@example.com") -> Desk:
    slug = await tenant(client, email)
    admin = await auth(client, slug, email)
    tid, admin_id = claims(admin)
    sam_id, sam = await staff(client, slug, admin)
    cust_id, cara = await customer(client, slug)
    if flag:
        r = await client.put(f"/t/{slug}/flags/{FLAG}", headers=admin, json={"enabled": True})
        assert r.status_code == 200, r.text
    return Desk(slug, tid, admin, admin_id, sam_id, sam, cust_id, cara)


async def _ticket(client: httpx.AsyncClient, d: Desk, **extra: object) -> dict[str, Any]:
    body = {"subject": "Broken", "body": "Help", "requester_id": d.cust_id, **extra}
    r = await client.post(f"/t/{d.slug}/tickets", headers=d.sam, json=body)
    assert r.status_code == 201, r.text
    ticket: dict[str, Any] = r.json()
    return ticket


async def _overdue(d: Desk, number: int, *columns: str) -> None:
    """Move deadlines one minute into the past, as if time had passed."""
    sets = ", ".join(f"{c} = now() - interval '1 minute'" for c in columns)
    async with tenant_session(d.tenant_id) as s:
        await s.execute(text(f"UPDATE tickets SET {sets} WHERE number = :n"), {"n": number})


async def _get(client: httpx.AsyncClient, d: Desk, number: int) -> dict[str, Any]:
    r = await client.get(f"/t/{d.slug}/tickets/{number}", headers=d.sam)
    assert r.status_code == 200, r.text
    ticket: dict[str, Any] = r.json()
    return ticket


async def _inbox(client: httpx.AsyncClient, slug: str, who: dict[str, str]) -> list[dict[str, Any]]:
    r = await client.get(f"/t/{slug}/notifications", headers=who)
    assert r.status_code == 200, r.text
    return [n for n in r.json()["items"] if n["kind"] == "sla_breached"]


async def test_td007_ac1_first_response_breach_is_flagged(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    late, answered = await _ticket(client, d), await _ticket(client, d)
    await client.post(
        f"/t/{d.slug}/tickets/{answered['number']}/messages", headers=d.sam, json={"body": "On it"}
    )
    for t in (late, answered):
        await _overdue(d, t["number"], "first_response_due_at")
    await sweep()
    flagged = await _get(client, d, late["number"])
    assert flagged["first_response_breached_at"] is not None
    assert flagged["breach"] == {
        "type": "first_response",
        "breached_at": flagged["first_response_breached_at"],
        "active": True,
    }
    assert (await _get(client, d, answered["number"]))["first_response_breached_at"] is None


async def test_td007_ac2_resolution_breach_is_flagged_unless_resolved(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    open_t, done = await _ticket(client, d), await _ticket(client, d)
    await client.patch(f"/t/{d.slug}/tickets/{done['number']}", headers=d.sam, json={"status": "resolved"})
    for t in (open_t, done):
        await _overdue(d, t["number"], "resolution_due_at")
    await sweep()
    assert (await _get(client, d, open_t["number"]))["resolution_breached_at"] is not None
    assert (await _get(client, d, done["number"]))["resolution_breached_at"] is None


async def test_td007_ac10_pending_customer_never_breaches_resolution(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    t = await _ticket(client, d)
    url = f"/t/{d.slug}/tickets/{t['number']}"
    await client.patch(url, headers=d.sam, json={"status": "open"})
    await client.patch(url, headers=d.sam, json={"status": "pending_customer"})
    await _overdue(d, t["number"], "resolution_due_at")
    await sweep()
    assert (await _get(client, d, t["number"]))["resolution_breached_at"] is None


async def test_td007_ac4_ac5_assignee_and_every_admin_notified(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    _, admin2 = await staff(client, d.slug, d.admin, "ali@example.com", role="admin")
    t = await _ticket(client, d)
    await client.patch(f"/t/{d.slug}/tickets/{t['number']}", headers=d.admin, json={"assignee_id": d.sam_id})
    await _overdue(d, t["number"], "first_response_due_at")
    await sweep()
    for who in (d.sam, d.admin, admin2):
        [n] = await _inbox(client, d.slug, who)
        assert n["ticket_id"] == t["id"]
        assert n["payload"] == {"number": t["number"], "subject": "Broken", "sla_type": "first_response"}
    assert await _inbox(client, d.slug, d.cara) == []  # customers are never told


async def test_td007_ac6_breach_is_audited(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    t = await _ticket(client, d)
    await _overdue(d, t["number"], "resolution_due_at")
    await sweep()
    async with tenant_session(d.tenant_id) as s:
        [entry] = (
            await s.execute(
                select(AuditEntry).where(
                    AuditEntry.entity_id == uuid.UUID(t["id"]), AuditEntry.action == "ticket.sla_breached"
                )
            )
        ).scalars()
    assert entry.actor_id is None  # the system, not a person
    assert entry.data["sla_type"] == "resolution"
    assert {"deadline", "detected_at"} <= set(entry.data)


async def test_td007_ac7_repeated_and_concurrent_sweeps_notify_once(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    t = await _ticket(client, d)
    # The assignee is also an admin: still one notification for them.
    await client.patch(
        f"/t/{d.slug}/tickets/{t['number']}", headers=d.admin, json={"assignee_id": str(d.admin_id)}
    )
    await _overdue(d, t["number"], "first_response_due_at")
    await asyncio.gather(sweep(), sweep())
    await sweep()
    assert len(await _inbox(client, d.slug, d.admin)) == 1
    async with tenant_session(d.tenant_id) as s:
        audits = await s.execute(
            select(AuditEntry).where(
                AuditEntry.entity_id == uuid.UUID(t["id"]), AuditEntry.action == "ticket.sla_breached"
            )
        )
        assert len(list(audits.scalars())) == 1


async def test_td007_ac8_sweep_never_crosses_tenants(client: httpx.AsyncClient) -> None:
    a = await _desk(client)
    b = await _desk(client, email="bob@example.com")
    ta, tb = await _ticket(client, a), await _ticket(client, b)
    await _overdue(a, ta["number"], "first_response_due_at")
    await _overdue(b, tb["number"], "first_response_due_at")
    result = await sweep()
    assert (a.tenant_id, uuid.UUID(ta["id"]), "first_response") in result.breaches
    assert [n["ticket_id"] for n in await _inbox(client, a.slug, a.admin)] == [ta["id"]]
    assert [n["ticket_id"] for n in await _inbox(client, b.slug, b.admin)] == [tb["id"]]


async def test_td007_ac11_ac13_reopen_and_priority_change_keep_breach(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    t = await _ticket(client, d)
    url = f"/t/{d.slug}/tickets/{t['number']}"
    await _overdue(d, t["number"], "resolution_due_at")
    await sweep()
    breached_at = (await _get(client, d, t["number"]))["resolution_breached_at"]
    await client.patch(url, headers=d.sam, json={"status": "resolved"})
    await client.post(f"{url}/messages", headers=d.cara, json={"body": "Broken again"})  # reopen
    await client.patch(url, headers=d.sam, json={"priority": "P4"})
    after = await _get(client, d, t["number"])
    assert after["status"] == "open"
    assert after["resolution_breached_at"] == breached_at  # never cleared
    assert after["breach"]["active"] is True  # reopened, so it needs action again


async def test_td007_ac12_first_reply_ends_active_breach_keeps_history(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    t = await _ticket(client, d)
    await _overdue(d, t["number"], "first_response_due_at")
    await sweep()
    await client.post(f"/t/{d.slug}/tickets/{t['number']}/messages", headers=d.sam, json={"body": "Sorry!"})
    after = await _get(client, d, t["number"])
    assert after["first_response_breached_at"] is not None
    assert after["breach"]["active"] is False


async def test_td007_ac14_flag_off_no_effect(client: httpx.AsyncClient) -> None:
    d = await _desk(client, flag=False)
    t = await _ticket(client, d)
    await _overdue(d, t["number"], "first_response_due_at", "resolution_due_at")
    await sweep()
    after = await _get(client, d, t["number"])
    assert after["first_response_breached_at"] is None
    assert after["resolution_breached_at"] is None
    assert await _inbox(client, d.slug, d.admin) == []


async def test_td007_flags_admin_only_and_known_keys(client: httpx.AsyncClient) -> None:
    d = await _desk(client, flag=False)
    assert (await client.get(f"/t/{d.slug}/flags", headers=d.admin)).json() == {FLAG: False}
    put = await client.put(f"/t/{d.slug}/flags/{FLAG}", headers=d.sam, json={"enabled": True})
    assert put.status_code == 403
    unknown = await client.put(f"/t/{d.slug}/flags/nope", headers=d.admin, json={"enabled": True})
    assert unknown.status_code == 404
    other = await _desk(client, flag=False, email="bob@example.com")
    cross = await client.put(f"/t/{d.slug}/flags/{FLAG}", headers=other.admin, json={"enabled": True})
    assert cross.status_code == 404


async def test_td007_ac7_racing_tenant_sweeps_without_the_lock_breach_once(client: httpx.AsyncClient) -> None:
    """The advisory lock is an optimisation; the UPDATE ... IS NULL guard alone must hold."""
    d = await _desk(client)
    t = await _ticket(client, d)
    await _overdue(d, t["number"], "first_response_due_at")

    async def one() -> list[tuple[uuid.UUID, str]]:
        async with tenant_session(d.tenant_id) as s:
            return await _sweep_tenant(s, d.tenant_id)

    first, second = await asyncio.gather(one(), one())
    assert len(first) + len(second) == 1
    assert len(await _inbox(client, d.slug, d.admin)) == 1


async def test_td007_ac11_ticket_resolved_before_deploy_does_not_breach_on_reopen(
    client: httpx.AsyncClient,
) -> None:
    d = await _desk(client)
    t = await _ticket(client, d, priority="P1")
    url = f"/t/{d.slug}/tickets/{t['number']}"
    await client.patch(url, headers=d.sam, json={"status": "resolved"})
    # Simulate a pre-td007 ticket: resolved two weeks ago, no pause recorded.
    async with tenant_session(d.tenant_id) as s:
        await s.execute(
            text(
                "UPDATE tickets SET paused_intervals = '[]'::jsonb, "
                "created_at = now() - interval '14 days 1 hour', resolved_at = now() - interval '14 days' "
                "WHERE number = :n"
            ),
            {"n": t["number"]},
        )
    await client.post(f"{url}/messages", headers=d.cara, json={"body": "Broken again"})
    await sweep()
    after = await _get(client, d, t["number"])
    assert after["status"] == "open"
    assert after["resolution_breached_at"] is None  # 1 h consumed of 8 h, not 14 days
