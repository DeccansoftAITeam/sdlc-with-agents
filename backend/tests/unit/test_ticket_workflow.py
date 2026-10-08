"""TD-004/AC-5 (unit): every (state, target) pair of the staff status machine."""

import pytest

from app.features.tickets import workflow

STATES = ("new", "open", "pending_customer", "resolved")
ALLOWED = {  # docs/specs/TD-004-ticket-workflow/spec.md, "Explicit staff status changes"
    ("new", "open"),
    ("new", "resolved"),
    ("open", "pending_customer"),
    ("open", "resolved"),
    ("pending_customer", "open"),
    ("pending_customer", "resolved"),
    ("resolved", "open"),
}


@pytest.mark.parametrize("current", STATES)
@pytest.mark.parametrize("target", STATES)
def test_td004_ac5_staff_transition_table(current: str, target: str) -> None:
    assert workflow.staff_can_move(current, target) == ((current, target) in ALLOWED)


@pytest.mark.parametrize(
    ("current", "after"),
    [("new", "open"), ("open", "open"), ("pending_customer", "pending_customer"), ("resolved", "resolved")],
)
def test_td004_staff_activity_opens_only_new_tickets(current: str, after: str) -> None:
    assert workflow.after_staff_activity(current) == after


@pytest.mark.parametrize(
    ("current", "after"),
    [("new", "new"), ("open", "open"), ("pending_customer", "open"), ("resolved", "open")],
)
def test_td004_ac4_customer_reply_reopens(current: str, after: str) -> None:
    assert workflow.after_customer_reply(current) == after
