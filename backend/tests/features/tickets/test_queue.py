"""TD-007/AC-3, AC-12, AC-14 (queue side): breach-active tickets float to the top."""

import httpx

from app.features.sla.sweep import sweep
from tests.features.sla.test_sweep import _desk, _overdue, _ticket


async def _queue(client: httpx.AsyncClient, slug: str, who: dict[str, str], **params: object) -> dict:  # type: ignore[type-arg]
    r = await client.get(f"/t/{slug}/tickets", headers=who, params=params)
    assert r.status_code == 200, r.text
    return r.json()  # type: ignore[no-any-return]


async def test_td007_ac3_breach_active_first_earliest_breach_first(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    first, second, calm, newest = [await _ticket(client, d) for _ in range(4)]
    await _overdue(d, first["number"], "first_response_due_at")
    await sweep()  # first breaches earlier ...
    await _overdue(d, second["number"], "resolution_due_at")
    await sweep()  # ... than second
    numbers = [t["number"] for t in (await _queue(client, d.slug, d.sam))["items"]]
    assert numbers == [first["number"], second["number"], newest["number"], calm["number"]]

    paged, cursor = [], None
    while True:  # the cursor keeps the same order across pages
        params: dict[str, object] = {"limit": 1}
        if cursor:
            params["cursor"] = cursor
        page = await _queue(client, d.slug, d.sam, **params)
        paged += [t["number"] for t in page["items"]]
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert paged == numbers


async def test_td007_ac12_answered_breach_stops_floating(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    old, new = await _ticket(client, d), await _ticket(client, d)
    await _overdue(d, old["number"], "first_response_due_at")
    await sweep()
    await client.post(f"/t/{d.slug}/tickets/{old['number']}/messages", headers=d.sam, json={"body": "Hi"})
    numbers = [t["number"] for t in (await _queue(client, d.slug, d.sam))["items"]]
    assert numbers == [new["number"], old["number"]]  # back to newest-first


async def test_td007_ac14_flag_off_stops_floating(client: httpx.AsyncClient) -> None:
    d = await _desk(client)
    old, new = await _ticket(client, d), await _ticket(client, d)
    await _overdue(d, old["number"], "first_response_due_at")
    await sweep()
    await client.put(f"/t/{d.slug}/flags/sla-breach-escalation", headers=d.admin, json={"enabled": False})
    items = (await _queue(client, d.slug, d.sam))["items"]
    assert [t["number"] for t in items] == [new["number"], old["number"]]
    assert items[1]["breach"]["active"] is False  # history kept, no longer escalated
    assert items[1]["first_response_breached_at"] is not None
