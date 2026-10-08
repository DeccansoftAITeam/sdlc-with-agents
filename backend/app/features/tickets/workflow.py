"""The ticket status machine (TD-004 status model). Pure: no I/O, fully unit-testable.

new ──(staff reply / assign / staff sets open)──► open
open ⇄ pending_customer                 (staff)
new | open | pending_customer ──► resolved   (staff)
pending_customer | resolved ──(customer reply)──► open
resolved ──(staff reopens)──► open
"""

STAFF_TRANSITIONS: dict[str, frozenset[str]] = {
    "new": frozenset({"open", "resolved"}),
    "open": frozenset({"pending_customer", "resolved"}),
    "pending_customer": frozenset({"open", "resolved"}),
    "resolved": frozenset({"open"}),
}


def staff_can_move(current: str, target: str) -> bool:
    return target in STAFF_TRANSITIONS.get(current, frozenset())


def after_staff_activity(current: str) -> str:
    """A staff reply or assignment opens a new ticket; other states are unchanged."""
    return "open" if current == "new" else current


def after_customer_reply(current: str) -> str:
    """A customer reply reopens a ticket that was waiting on them or resolved."""
    return "open" if current in ("pending_customer", "resolved") else current
