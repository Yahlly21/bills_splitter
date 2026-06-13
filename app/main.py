"""FastAPI application: JSON endpoints + static frontend.

Endpoints follow SPEC §5. State lives in the in-memory `store`; the frontend is
a single `static/index.html` served at the root.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import calc, store
from app.models import Bill, EvenSplitRequest, Item, ItemsUpdate, SettleRequest

load_dotenv()

app = FastAPI(title="Friday Brunch Bill Splitter")

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


# --- Serialization --------------------------------------------------------


def _item_dict(item: Item) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "price": item.price,
        "remaining": item.remaining,
    }


def _bill_dict(bill: Bill) -> dict:
    return {
        "id": bill.id,
        "items": [_item_dict(i) for i in bill.items],
        "tip_pct": bill.tip_pct,
        "finalized": bill.finalized,
        "settled": [r.model_dump() for r in bill.settled],
    }


def _require_bill(bill_id: str) -> Bill:
    bill = store.get(bill_id)
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


# --- API ------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/bills")
def create_bill() -> dict:
    bill = store.create()
    return _bill_dict(bill)


@app.get("/api/bills/{bill_id}")
def get_bill(bill_id: str) -> dict:
    return _bill_dict(_require_bill(bill_id))


@app.put("/api/bills/{bill_id}/items")
def replace_items(bill_id: str, payload: ItemsUpdate) -> dict:
    bill = _require_bill(bill_id)
    # Explode any qty > 1 into separate, fully-priced rows (SPEC §6.3).
    items: list[Item] = []
    for entry in payload.items:
        for _ in range(entry.qty):
            items.append(
                Item(name=entry.name, price=entry.price, remaining=entry.price)
            )
    bill.items = items
    bill.original_subtotal = calc.round2(sum(i.price for i in items))
    bill.finalized = False  # editing the table re-opens the finalize gate
    store.save(bill)
    return _bill_dict(bill)


@app.post("/api/bills/{bill_id}/extract")
async def extract(bill_id: str, image: UploadFile) -> dict:
    _require_bill(bill_id)
    from app import llm  # imported lazily so the app boots without an API key

    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="No image was uploaded")

    try:
        result = llm.extract_items(data, media_type=image.content_type or "image/jpeg")
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # network / auth / API errors → graceful fallback
        raise HTTPException(
            status_code=502,
            detail=f"Receipt extraction failed: {exc}. You can enter the bill manually.",
        ) from exc

    # Extraction does not auto-commit — the frontend loads these into the table.
    return result


@app.post("/api/bills/{bill_id}/finalize")
def finalize(bill_id: str) -> dict:
    bill = _require_bill(bill_id)
    if not bill.items:
        raise HTTPException(status_code=400, detail="Cannot finalize an empty bill")
    bill.finalized = True
    store.save(bill)
    return _bill_dict(bill)


@app.post("/api/bills/{bill_id}/split/even")
def split_even(bill_id: str, req: EvenSplitRequest) -> dict:
    bill = _require_bill(bill_id)
    if not bill.finalized:
        raise HTTPException(
            status_code=400, detail="Finalize the bill before splitting"
        )
    if not bill.items:
        raise HTTPException(status_code=400, detail="No items to split")
    subtotal = sum(i.price for i in bill.items)
    bill.tip_pct = req.tip_pct
    store.save(bill)
    return calc.even_split(subtotal, req.people, req.tip_pct)


@app.post("/api/bills/{bill_id}/settle")
def settle(bill_id: str, req: SettleRequest) -> dict:
    bill = _require_bill(bill_id)
    if not bill.finalized:
        raise HTTPException(status_code=400, detail="Finalize the bill before settling")
    if not req.claims:
        raise HTTPException(status_code=400, detail="No items selected for this batch")
    try:
        result = calc.settle(bill, req.name, req.claims, req.tip_pct)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.save(bill)
    return result


# --- Static frontend ------------------------------------------------------


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
