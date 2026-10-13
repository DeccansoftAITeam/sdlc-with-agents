"""TD-008/AC-6 and AC-8 (budget side): per-tenant monthly tokens and per-minute requests."""

import uuid

import httpx
import pytest

from app.core.db import tenant_session
from app.features.ai import budget
from tests.features.helpers import auth, claims, tenant


async def _tenant(client: httpx.AsyncClient) -> uuid.UUID:
    slug = await tenant(client)
    tid, _ = claims(await auth(client, slug))
    return tid


async def test_td008_ac6_monthly_token_cap(client: httpx.AsyncClient) -> None:
    tid = await _tenant(client)
    async with tenant_session(tid) as s:
        await budget.reserve(s, tid)  # empty ledger: allowed
        await budget.record(s, tid, budget.MONTHLY_TOKENS - 10, 9)
        await budget.reserve(s, tid)  # 1 token left: still allowed
        await budget.record(s, tid, 0, 1)
        with pytest.raises(budget.BudgetExceeded) as e:
            await budget.reserve(s, tid)
        assert e.value.reason == "monthly"
        assert await budget.used_tokens(s) == budget.MONTHLY_TOKENS


async def test_td008_ac6_twenty_requests_per_minute(client: httpx.AsyncClient) -> None:
    tid = await _tenant(client)
    async with tenant_session(tid) as s:
        for _ in range(budget.REQUESTS_PER_MINUTE):
            await budget.reserve(s, tid)
        with pytest.raises(budget.BudgetExceeded) as e:
            await budget.reserve(s, tid)
        assert e.value.reason == "rate"


async def test_td008_ac8_usage_is_per_tenant(client: httpx.AsyncClient) -> None:
    a, b = await _tenant(client), await _tenant(client)
    async with tenant_session(a) as s:
        await budget.record(s, a, budget.MONTHLY_TOKENS, 0)
        with pytest.raises(budget.BudgetExceeded):
            await budget.reserve(s, a)
    async with tenant_session(b) as s:
        assert await budget.used_tokens(s) == 0  # RLS: A's ledger is invisible to B
        await budget.reserve(s, b)
