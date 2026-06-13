"""API endpoint tests (SPEC §5). The LLM extract path is not exercised here —
it needs a live API key and is covered by manual/verify runs."""

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_store():
    store.clear()
    yield
    store.clear()


def _new_bill() -> str:
    return client.post("/api/bills").json()["id"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_get_bill():
    bid = _new_bill()
    res = client.get(f"/api/bills/{bid}")
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_get_unknown_bill_404():
    assert client.get("/api/bills/nope").status_code == 404


def test_put_items_explodes_qty():
    bid = _new_bill()
    res = client.put(
        f"/api/bills/{bid}/items",
        json={"items": [{"name": "Latte", "price": 4.5, "qty": 3}]},
    )
    items = res.json()["items"]
    assert len(items) == 3
    assert all(i["name"] == "Latte" and i["price"] == 4.5 for i in items)
    assert all(i["remaining"] == 4.5 for i in items)


def test_negative_price_rejected():
    bid = _new_bill()
    res = client.put(
        f"/api/bills/{bid}/items",
        json={"items": [{"name": "Bad", "price": -1, "qty": 1}]},
    )
    assert res.status_code == 422


def test_finalize_empty_bill_blocked():
    bid = _new_bill()
    res = client.post(f"/api/bills/{bid}/finalize")
    assert res.status_code == 400


def test_finalize_ok():
    bid = _new_bill()
    client.put(
        f"/api/bills/{bid}/items", json={"items": [{"name": "Eggs", "price": 12}]}
    )
    res = client.post(f"/api/bills/{bid}/finalize")
    assert res.status_code == 200
    assert res.json()["finalized"] is True


def _finalized_bill(items: list) -> str:
    bid = _new_bill()
    client.put(f"/api/bills/{bid}/items", json={"items": items})
    client.post(f"/api/bills/{bid}/finalize")
    return bid


def test_split_requires_finalize():
    bid = _new_bill()
    client.put(f"/api/bills/{bid}/items", json={"items": [{"name": "A", "price": 10}]})
    res = client.post(f"/api/bills/{bid}/split/even", json={"people": 2, "tip_pct": 10})
    assert res.status_code == 400


def test_settle_requires_finalize():
    bid = _new_bill()
    client.put(f"/api/bills/{bid}/items", json={"items": [{"name": "A", "price": 10}]})
    bill = client.get(f"/api/bills/{bid}").json()
    res = client.post(
        f"/api/bills/{bid}/settle",
        json={"claims": [{"item_id": bill["items"][0]["id"]}], "tip_pct": 10},
    )
    assert res.status_code == 400


def test_even_split_endpoint():
    bid = _finalized_bill([{"name": "A", "price": 50}, {"name": "B", "price": 50}])
    res = client.post(f"/api/bills/{bid}/split/even", json={"people": 2, "tip_pct": 20})
    body = res.json()
    assert body["total"] == 120.0
    assert body["per_person"] == [60.0, 60.0]


def test_even_split_blank_tip_is_422():
    bid = _new_bill()
    client.put(f"/api/bills/{bid}/items", json={"items": [{"name": "A", "price": 10}]})
    res = client.post(f"/api/bills/{bid}/split/even", json={"people": 2})
    assert res.status_code == 422


def test_even_split_people_min_enforced():
    bid = _new_bill()
    client.put(f"/api/bills/{bid}/items", json={"items": [{"name": "A", "price": 10}]})
    res = client.post(f"/api/bills/{bid}/split/even", json={"people": 0, "tip_pct": 10})
    assert res.status_code == 422


def test_settle_flow_end_to_end():
    bid = _finalized_bill(
        [{"name": "Pancakes", "price": 14}, {"name": "Juice", "price": 6}]
    )
    bill = client.get(f"/api/bills/{bid}").json()
    id1, id2 = bill["items"][0]["id"], bill["items"][1]["id"]

    r1 = client.post(
        f"/api/bills/{bid}/settle",
        json={"name": "Dana", "claims": [{"item_id": id1}], "tip_pct": 18},
    ).json()
    assert len(r1["remaining_items"]) == 1
    assert r1["all_settled"] is False

    r2 = client.post(
        f"/api/bills/{bid}/settle",
        json={"name": "Sam", "claims": [{"item_id": id2}], "tip_pct": 18},
    ).json()
    assert r2["all_settled"] is True
    assert r2["totals"]["total_tip_amount"] == round(14 * 0.18 + 6 * 0.18, 2)


def test_settle_empty_claims_rejected():
    bid = _finalized_bill([{"name": "A", "price": 10}])
    res = client.post(f"/api/bills/{bid}/settle", json={"claims": [], "tip_pct": 10})
    assert res.status_code == 400


def test_index_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "Bill" in res.text
