"""Core money math for the bill splitter.

All amounts are tax-inclusive (SPEC §2). Rounding happens at the cent. The two
split methods live here so they can be unit-tested in isolation from FastAPI.
"""

from __future__ import annotations

from app.models import Bill, Claim, SettledRecord

# Items are dropped once their balance is within half a cent of zero (SPEC §7).
REMOVE_EPSILON = 0.005
# Below this overall effective tip %, the UI shows a gentle nudge (SPEC §6.6).
LOW_TIP_THRESHOLD = 10.0


def round2(x: float) -> float:
    """Round to cents. `+ 0.0` normalises any negative zero to 0.0."""
    return round(x + 0.0, 2)


def even_split(subtotal: float, people: int, tip_pct: float) -> dict:
    """Split `subtotal × (1 + tip)` across `people`.

    Returns each person's share. The last person absorbs the rounding
    remainder so the shares sum back to the grand total exactly (SPEC §6.5).
    """
    if people < 1:
        raise ValueError("people must be at least 1")

    tip_amount = round2(subtotal * tip_pct / 100)
    total = round2(subtotal + tip_amount)

    per = round2(total / people)
    shares = [per] * (people - 1)
    shares.append(round2(total - per * (people - 1)))

    return {
        "people": people,
        "subtotal": round2(subtotal),
        "tip_pct": tip_pct,
        "tip_amount": tip_amount,
        "total": total,
        "per_person": shares,
    }


def compute_totals(bill: Bill) -> dict:
    """Aggregate the live state of an individual-mode bill.

    The denominator for the overall tip % is the original item subtotal —
    recoverable as (paid subtotal + remaining), since each claim reduces an
    item's `remaining` by exactly the claimed amount (SPEC §7).
    """
    paid_subtotal = sum(r.subtotal for r in bill.settled)
    total_tip_amount = sum(r.tip_amount for r in bill.settled)
    remaining_amount = sum(i.remaining for i in bill.items)
    # Prefer the original price sum (set when the table was saved); fall back to
    # the reconstructed sum for bills built directly in unit tests.
    original_subtotal = bill.original_subtotal or (paid_subtotal + remaining_amount)

    overall_tip_pct = (
        (total_tip_amount / original_subtotal * 100) if original_subtotal > 0 else 0.0
    )

    return {
        "paid_so_far": round2(paid_subtotal + total_tip_amount),
        "remaining_amount": round2(remaining_amount),
        "total_tip_amount": round2(total_tip_amount),
        "overall_tip_pct": round2(overall_tip_pct),
    }


def settle(bill: Bill, name: str | None, claims: list[Claim], tip_pct: float) -> dict:
    """Apply one settled batch: reduce balances, drop emptied items, log it.

    For each claim the claimed amount is `price / divide_by` (the ÷N control),
    referencing the item's full price. The batch total is `Σ claimed × (1 + tip)`.
    Returns the full updated picture (settlement + remaining + log + totals).
    """
    items_by_id = {i.id: i for i in bill.items}
    covered: list[dict] = []
    subtotal = 0.0

    for claim in claims:
        item = items_by_id.get(claim.item_id)
        if item is None:
            raise KeyError(f"unknown item_id: {claim.item_id}")
        claimed = item.price / claim.divide_by
        item.remaining = round2(item.remaining - claimed)
        subtotal += claimed
        covered.append({"name": item.name, "amount": round2(claimed)})

    # Drop any item whose balance has hit zero.
    bill.items = [i for i in bill.items if i.remaining > REMOVE_EPSILON]

    subtotal = round2(subtotal)
    tip_amount = round2(subtotal * tip_pct / 100)
    total = round2(subtotal + tip_amount)

    record = SettledRecord(
        name=(name.strip() or None) if name else None,
        items=covered,
        subtotal=subtotal,
        tip_pct=tip_pct,
        tip_amount=tip_amount,
        total=total,
    )
    bill.settled.append(record)

    totals = compute_totals(bill)
    all_settled = len(bill.items) == 0
    low_tip = all_settled and totals["overall_tip_pct"] < LOW_TIP_THRESHOLD

    return {
        "settlement": {
            "name": record.name,
            "items": record.items,
            "subtotal": record.subtotal,
            "tip_pct": record.tip_pct,
            "tip_amount": record.tip_amount,
            "total": record.total,
        },
        "remaining_items": [
            {"id": i.id, "name": i.name, "price": i.price, "remaining": i.remaining}
            for i in bill.items
        ],
        "settled": [r.model_dump() for r in bill.settled],
        "totals": totals,
        "all_settled": all_settled,
        "low_tip": low_tip,
    }
