"""Pydantic models for the Friday Brunch Bill Splitter.

The schemas here are the single source of truth for validation. They mirror
`docs/spec/SPEC.md` §4 (data model) and §5 (API request/response shapes).
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# --- Core domain ----------------------------------------------------------


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class Item(BaseModel):
    """A single, fully-exploded line item (tax-inclusive)."""

    id: str = Field(default_factory=_new_id)
    name: str
    price: float
    remaining: float

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("price")
    @classmethod
    def _price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price must be greater than 0")
        return round(float(v), 2)


class SettledRecord(BaseModel):
    """Audit-trail entry for one settled batch (individual mode only)."""

    name: Optional[str] = None
    items: list[dict] = Field(default_factory=list)  # [{name, amount}]
    subtotal: float
    tip_pct: float
    tip_amount: float
    total: float


class Bill(BaseModel):
    """The whole in-memory bill state, keyed by `id` in the store."""

    id: str = Field(default_factory=_new_id)
    items: list[Item] = Field(default_factory=list)
    tip_pct: float = 0
    finalized: bool = False
    settled: list[SettledRecord] = Field(default_factory=list)
    # Σ of all item prices when the table was saved — the fixed denominator for
    # the overall effective tip % (items get removed as they settle).
    original_subtotal: float = 0


# --- LLM extraction -------------------------------------------------------


class ExtractedItem(BaseModel):
    """One final, per-unit row produced by the LLM (no qty)."""

    name: str
    price: float


class ExtractedBill(BaseModel):
    items: list[ExtractedItem]


# --- API request bodies ---------------------------------------------------


class ItemIn(BaseModel):
    """An item as entered in the table. `qty` is exploded server-side."""

    name: str
    price: float
    qty: int = 1

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @field_validator("price")
    @classmethod
    def _price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price must be greater than 0")
        return round(float(v), 2)

    @field_validator("qty")
    @classmethod
    def _qty_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("qty must be at least 1")
        return v


class ItemsUpdate(BaseModel):
    items: list[ItemIn] = Field(default_factory=list)


class EvenSplitRequest(BaseModel):
    people: int
    tip_pct: float

    @field_validator("people")
    @classmethod
    def _people_min(cls, v: int) -> int:
        if v < 1:
            raise ValueError("people must be at least 1")
        return v

    @field_validator("tip_pct")
    @classmethod
    def _tip_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("tip_pct must be 0 or greater")
        return v


class Claim(BaseModel):
    """A claim against one item; `divide_by` implements the per-row ÷N control."""

    item_id: str
    divide_by: int = 1

    @field_validator("divide_by")
    @classmethod
    def _divide_min(cls, v: int) -> int:
        if v < 1:
            raise ValueError("divide_by must be at least 1")
        return v


class SettleRequest(BaseModel):
    name: Optional[str] = None
    claims: list[Claim] = Field(default_factory=list)
    tip_pct: float

    @field_validator("tip_pct")
    @classmethod
    def _tip_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("tip_pct must be 0 or greater")
        return v
