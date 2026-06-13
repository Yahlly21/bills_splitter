"""In-memory bill store.

A plain process-local dict keyed by `bill_id`. State evaporates on restart or
idle — a deliberate trade-off for this single-user, one-time-use tool
(see SPEC §3). No DB, no persistence.
"""

from __future__ import annotations

from app.models import Bill

_bills: dict[str, Bill] = {}


def create() -> Bill:
    bill = Bill()
    _bills[bill.id] = bill
    return bill


def get(bill_id: str) -> Bill | None:
    return _bills.get(bill_id)


def save(bill: Bill) -> None:
    _bills[bill.id] = bill


def clear() -> None:
    """Reset the store (used by tests)."""
    _bills.clear()
