"""TD-005/AC-3…6: SLA deadlines. Pure: no I/O and no `now()`, so every rule is unit-testable.

P1 counts wall-clock time 24x7; P2-P4 count only inside the tenant's weekly schedule, in
the tenant's timezone (zoneinfo handles DST). `pending_customer` pauses delay the
resolution deadline only. Deadlines are never restarted (constitution §8).
"""

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ROUND_THE_CLOCK = frozenset({"P1"})
MAX_DAYS = 366 * 3  # far beyond the largest allowed target; stops a runaway loop

Pause = tuple[datetime, datetime | None]  # end None = still paused
Segment = tuple[datetime, datetime | None]  # end None = open-ended


@dataclass(frozen=True)
class Target:
    first_response_minutes: int
    resolution_minutes: int


@dataclass(frozen=True)
class Schedule:
    days: frozenset[int]  # 0 = Monday
    start: time
    end: time


@dataclass(frozen=True)
class Deadlines:
    first_response_due_at: datetime
    resolution_due_at: datetime | None  # None while the ticket is paused


def compute_deadlines(
    created_at: datetime,
    priority: str,
    paused_intervals: Sequence[Pause],
    targets: Mapping[str, Target],
    schedule: Schedule,
    tz: str,
) -> Deadlines:
    target = targets[priority]
    start = created_at.astimezone(UTC)
    always = priority in ROUND_THE_CLOCK
    first = _add(_working(start, always, schedule, tz), target.first_response_minutes)
    if any(end is None for _, end in paused_intervals):
        return Deadlines(first, None)
    counted = (
        piece for seg in _working(start, always, schedule, tz) for piece in _minus(seg, paused_intervals)
    )
    return Deadlines(first, _add(counted, target.resolution_minutes))


def _working(start: datetime, always: bool, schedule: Schedule, tz: str) -> Iterator[Segment]:
    if always:
        yield (start, None)
        return
    zone = ZoneInfo(tz)
    day: date = start.astimezone(zone).date()
    for _ in range(MAX_DAYS):
        if day.weekday() in schedule.days:
            opens = datetime.combine(day, schedule.start, zone).astimezone(UTC)
            closes = datetime.combine(day, schedule.end, zone).astimezone(UTC)
            if closes > max(opens, start):
                yield (max(opens, start), closes)
        day += timedelta(days=1)


def _minus(segment: Segment, pauses: Sequence[Pause]) -> list[Segment]:
    pieces = [segment]
    for p_start, p_end in pauses:
        assert p_end is not None  # open pauses are handled by the caller
        kept: list[Segment] = []
        for a, b in pieces:
            if p_end <= a or (b is not None and p_start >= b):
                kept.append((a, b))
                continue
            if p_start > a:
                kept.append((a, p_start))
            if b is None or p_end < b:
                kept.append((p_end, b))
        pieces = kept
    return pieces


def _add(segments: Iterator[Segment], minutes: int) -> datetime:
    remaining = timedelta(minutes=minutes)
    for a, b in segments:
        if b is None or a + remaining <= b:
            return a + remaining
        remaining -= b - a
    raise ValueError("SLA target can't be met within the schedule horizon")
