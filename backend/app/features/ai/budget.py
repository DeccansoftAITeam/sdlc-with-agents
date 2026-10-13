"""TD-008/AC-6, ADR-0004: per-tenant AI limits, checked before every model call.

`reserve` refuses when the month's tokens are spent or the tenant made 20 calls in the last
minute; `record` adds the provider-reported usage afterwards. One in-flight call may overshoot
the monthly cap slightly (accepted: the next call is refused).
"""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ratelimit
from app.features.ai.models import Usage

MONTHLY_TOKENS = 200_000
REQUESTS_PER_MINUTE = 20


class BudgetExceeded(Exception):
    def __init__(self, reason: str) -> None:  # "monthly" | "rate"
        super().__init__(reason)
        self.reason = reason


def _month() -> date:
    return datetime.now(UTC).date().replace(day=1)  # calendar month in UTC


async def used_tokens(s: AsyncSession) -> int:
    """Tokens used this month by the session's tenant (RLS scopes the row)."""
    total = await s.scalar(
        select(func.coalesce(Usage.input_tokens + Usage.output_tokens, 0)).where(Usage.month == _month())
    )
    return int(total or 0)


async def reserve(s: AsyncSession, tenant_id: uuid.UUID) -> None:
    if await used_tokens(s) >= MONTHLY_TOKENS:
        raise BudgetExceeded("monthly")
    try:
        ratelimit.hit(f"ai:{tenant_id}", REQUESTS_PER_MINUTE, 60)
    except ratelimit.RateLimited:
        raise BudgetExceeded("rate") from None


async def record(s: AsyncSession, tenant_id: uuid.UUID, input_tokens: int, output_tokens: int) -> None:
    stmt = insert(Usage).values(
        tenant_id=tenant_id,
        month=_month(),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        requests=1,
    )
    await s.execute(
        stmt.on_conflict_do_update(
            constraint="pk_ai_usage",
            set_={
                "input_tokens": Usage.input_tokens + stmt.excluded.input_tokens,
                "output_tokens": Usage.output_tokens + stmt.excluded.output_tokens,
                "requests": Usage.requests + 1,
            },
        )
    )
