"""Unit tests for the money math (SPEC §7)."""

from app import calc
from app.models import Bill, Claim, Item


def _bill(*prices: float) -> Bill:
    items = [Item(name=f"item{i}", price=p, remaining=p) for i, p in enumerate(prices)]
    return Bill(items=items)


# --- Even split -----------------------------------------------------------


def test_even_split_no_tip_last_absorbs_remainder():
    res = calc.even_split(10.00, 3, 0)
    assert res["per_person"] == [3.33, 3.33, 3.34]
    assert sum(res["per_person"]) == 10.00
    assert res["total"] == 10.00


def test_even_split_with_tip():
    res = calc.even_split(100.00, 2, 20)
    assert res["tip_amount"] == 20.00
    assert res["total"] == 120.00
    assert res["per_person"] == [60.00, 60.00]


def test_even_split_single_person_gets_everything():
    res = calc.even_split(42.50, 1, 10)
    assert res["per_person"] == [46.75]


def test_even_split_shares_sum_to_total():
    res = calc.even_split(33.33, 7, 18)
    assert round(sum(res["per_person"]), 2) == res["total"]


# --- Settle and remove ----------------------------------------------------


def test_settle_whole_item_removes_it():
    bill = _bill(10.0, 6.0)
    item_id = bill.items[0].id
    res = calc.settle(bill, "Dana", [Claim(item_id=item_id)], 10)

    assert res["settlement"]["subtotal"] == 10.0
    assert res["settlement"]["tip_amount"] == 1.0
    assert res["settlement"]["total"] == 11.0
    assert len(bill.items) == 1  # the $10 item is gone
    assert res["all_settled"] is False


def test_shared_item_divn_clears_after_two_batches():
    bill = _bill(6.0)
    item_id = bill.items[0].id

    calc.settle(bill, "Ada", [Claim(item_id=item_id, divide_by=2)], 0)
    assert len(bill.items) == 1
    assert bill.items[0].remaining == 3.0

    res = calc.settle(bill, "Ben", [Claim(item_id=item_id, divide_by=2)], 0)
    assert len(bill.items) == 0
    assert res["all_settled"] is True


def test_tips_are_summed_not_averaged():
    bill = _bill(10.0, 6.0)
    id1, id2 = bill.items[0].id, bill.items[1].id

    calc.settle(bill, "A", [Claim(item_id=id1)], 10)  # tip 1.00
    res = calc.settle(bill, "B", [Claim(item_id=id2)], 20)  # tip 1.20

    totals = res["totals"]
    assert totals["total_tip_amount"] == 2.20  # 1.00 + 1.20, never averaged
    # overall tip % is over item subtotals only: 2.20 / 16 * 100
    assert totals["overall_tip_pct"] == 13.75
    assert res["all_settled"] is True


def test_low_tip_nudge_flag():
    bill = _bill(20.0)
    res = calc.settle(bill, None, [Claim(item_id=bill.items[0].id)], 5)
    assert res["all_settled"] is True
    assert res["low_tip"] is True


def test_healthy_tip_no_nudge():
    bill = _bill(20.0)
    res = calc.settle(bill, None, [Claim(item_id=bill.items[0].id)], 18)
    assert res["low_tip"] is False


def test_overall_tip_pct_zero_when_nothing_settled_subtotal():
    bill = _bill(10.0)
    # partial claim leaves a balance; overall % still computed over the original subtotal
    res = calc.settle(bill, None, [Claim(item_id=bill.items[0].id, divide_by=2)], 0)
    assert res["totals"]["overall_tip_pct"] == 0.0
    assert res["totals"]["remaining_amount"] == 5.0
