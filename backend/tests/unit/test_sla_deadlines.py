"""TD-005/AC-3…6 (unit): the pure SLA deadline function, examples + properties."""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from hypothesis import given, settings
from hypothesis import strategies as st

from app.features.sla.deadlines import Schedule, Target, compute_deadlines

WEEKDAYS = Schedule(days=frozenset(range(5)), start=time(9), end=time(18))
TARGETS = {
    "P1": Target(60, 480),
    "P2": Target(240, 540),
    "P3": Target(540, 1620),
    "P4": Target(1620, 5400),
}


def at(s: str, tz: str = "UTC") -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(tz))


def test_p1_counts_around_the_clock() -> None:  # AC-4
    d = compute_deadlines(at("2026-10-09T23:00"), "P1", [], TARGETS, WEEKDAYS, "UTC")  # Friday night
    assert d.first_response_due_at == at("2026-10-10T00:00")
    assert d.resolution_due_at == at("2026-10-10T07:00")


def test_p2_skips_the_weekend() -> None:  # AC-4
    d = compute_deadlines(at("2026-10-09T17:00"), "P2", [], TARGETS, WEEKDAYS, "UTC")
    assert d.first_response_due_at == at("2026-10-12T12:00")  # 1 h Fri + 3 h Mon
    assert d.resolution_due_at == at("2026-10-12T17:00")  # 1 h Fri + 8 h Mon


def test_created_before_hours_starts_at_opening() -> None:
    d = compute_deadlines(at("2026-10-07T06:00"), "P3", [], TARGETS, WEEKDAYS, "UTC")
    assert d.first_response_due_at == at("2026-10-07T18:00")  # one full business day


def test_business_hours_follow_the_tenant_timezone_across_dst() -> None:  # AC-6
    # New York springs forward on Sunday 2026-03-08: Friday is UTC-5, Monday is UTC-4.
    ny = "America/New_York"
    d = compute_deadlines(at("2026-03-06T17:00", ny), "P2", [], TARGETS, WEEKDAYS, ny)
    due = d.first_response_due_at.astimezone(ZoneInfo(ny))
    assert (due.date().isoformat(), due.time()) == ("2026-03-09", time(12))
    assert due.utcoffset() == timedelta(hours=-4)


def test_pauses_delay_resolution_only() -> None:  # AC-5
    created = at("2026-10-07T10:00")
    pause = (at("2026-10-07T11:00"), at("2026-10-07T13:00"))
    plain = compute_deadlines(created, "P1", [], TARGETS, WEEKDAYS, "UTC")
    paused = compute_deadlines(created, "P1", [pause], TARGETS, WEEKDAYS, "UTC")
    assert paused.first_response_due_at == plain.first_response_due_at
    assert paused.resolution_due_at == plain.resolution_due_at + timedelta(hours=2)


def test_pause_outside_business_hours_costs_nothing() -> None:
    created = at("2026-10-07T10:00")
    night = (at("2026-10-07T19:00"), at("2026-10-08T08:00"))
    plain = compute_deadlines(created, "P3", [], TARGETS, WEEKDAYS, "UTC")
    assert compute_deadlines(created, "P3", [night], TARGETS, WEEKDAYS, "UTC") == plain


def test_open_pause_means_no_resolution_deadline_yet() -> None:
    created = at("2026-10-07T10:00")
    d = compute_deadlines(created, "P2", [(at("2026-10-07T11:00"), None)], TARGETS, WEEKDAYS, "UTC")
    assert d.resolution_due_at is None
    assert d.first_response_due_at == at("2026-10-07T14:00")


def test_several_and_overlapping_pauses_count_once() -> None:  # AC-5
    created = at("2026-10-07T10:00")
    pauses = [
        (at("2026-10-07T11:00"), at("2026-10-07T12:00")),
        (at("2026-10-07T11:30"), at("2026-10-07T12:30")),  # overlaps the first
        (at("2026-10-07T14:00"), at("2026-10-07T14:15")),
    ]
    plain = compute_deadlines(created, "P1", [], TARGETS, WEEKDAYS, "UTC")
    paused = compute_deadlines(created, "P1", pauses, TARGETS, WEEKDAYS, "UTC")
    assert paused.resolution_due_at == plain.resolution_due_at + timedelta(minutes=105)


ZONES = ["UTC", "America/New_York", "Europe/London", "Asia/Kolkata", "Australia/Sydney"]
instants = st.datetimes(
    min_value=datetime(2024, 1, 1), max_value=datetime(2030, 12, 31), timezones=st.just(UTC)
)


@settings(max_examples=200, deadline=None)
@given(created=instants, tz=st.sampled_from(ZONES), a=st.integers(1, 6000), b=st.integers(1, 6000))
def test_monotonic_in_duration(created: datetime, tz: str, a: int, b: int) -> None:  # AC-6
    lo, hi = sorted((a, b))
    targets = {"P3": Target(lo, hi)}
    d = compute_deadlines(created, "P3", [], targets, WEEKDAYS, tz)
    assert created < d.first_response_due_at <= d.resolution_due_at  # type: ignore[operator]


@settings(max_examples=200, deadline=None)
@given(created=instants, tz=st.sampled_from(ZONES), minutes=st.integers(1, 6000))
def test_deadline_never_in_non_working_time(created: datetime, tz: str, minutes: int) -> None:  # AC-6
    due = compute_deadlines(created, "P4", [], {"P4": Target(minutes, minutes)}, WEEKDAYS, tz)
    local = due.first_response_due_at.astimezone(ZoneInfo(tz))
    assert local.weekday() < 5
    assert time(9) < local.time() <= time(18)
