"""Claude receipt extraction.

Turns a photographed receipt into a list of final, per-unit `{name, price}`
rows that drop straight into the editable table. Implements SPEC §8:

- One-shot prompt: the prompt embeds `docs/receipt_example.jpg` paired with its
  exact expected JSON output as a worked example.
- Structured output: the response is constrained to a JSON schema via the
  Anthropic SDK's `output_config.format`, then each row is validated against the
  `ExtractedItem` model. Rows that fail validation are dropped and surfaced to
  the caller rather than crashing the request.
- The uploaded image is never stored — it lives only for the duration of the call.
"""

from __future__ import annotations

import base64
import json
from functools import lru_cache
from pathlib import Path

import anthropic
from pydantic import ValidationError

from app.models import ExtractedItem

MODEL = "claude-opus-4-8"

_EXAMPLE_IMAGE = Path(__file__).resolve().parent.parent / "docs" / "receipt_example.jpg"

# The ideal extraction for the example receipt (SPEC §8). The `2 X 6.60` line is
# split into two separate per-unit rows; subtotal / VAT / total rows are ignored.
_EXAMPLE_OUTPUT = {
    "items": [
        {"name": "גבינת עמק 9%", "price": 36.90},
        {"name": "קוטג' 5% תנובה 250 גר", "price": 6.60},
        {"name": "קוטג' 5% תנובה 250 גר", "price": 6.60},
        {"name": "שקית ללקוח", "price": 0.10},
    ]
}

_INSTRUCTION = (
    "Extract every line item from this receipt as final, per-unit rows. "
    "Return a JSON array of {name, price}; ignore subtotal / tax / total / tip "
    "rows; prices as numbers. If a line shows a quantity (e.g. `2 X 6.60`), emit "
    "one row per unit at the unit price — never a combined line."
)

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                },
                "required": ["name", "price"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


@lru_cache(maxsize=1)
def _example_image_b64() -> str:
    return base64.standard_b64encode(_EXAMPLE_IMAGE.read_bytes()).decode("utf-8")


def _image_block(data_b64: str, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data_b64},
    }


def extract_items(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Extract items from a receipt image.

    Returns ``{"items": [...], "warnings": [...]}``. `items` are dicts ready for
    the table; `warnings` describe any rows that were dropped during validation.
    Raises ``RuntimeError`` on a malformed model response so the API layer can
    fall back to manual entry gracefully.
    """
    client = anthropic.Anthropic()
    target_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        # One-shot worked example: example receipt -> exact expected JSON.
        messages=[
            {
                "role": "user",
                "content": [
                    _image_block(_example_image_b64(), "image/jpeg"),
                    {"type": "text", "text": _INSTRUCTION},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": json.dumps(_EXAMPLE_OUTPUT, ensure_ascii=False)}
                ],
            },
            {
                "role": "user",
                "content": [
                    _image_block(target_b64, media_type),
                    {"type": "text", "text": _INSTRUCTION},
                ],
            },
        ],
        output_config={"format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA}},
    )

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        raw = json.loads(text)
        raw_items = raw["items"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError("Could not parse the receipt — try again or enter it manually.") from exc

    items: list[dict] = []
    warnings: list[str] = []
    for idx, candidate in enumerate(raw_items):
        try:
            extracted = ExtractedItem.model_validate(candidate)
            if extracted.price <= 0:
                raise ValueError("price must be greater than 0")
            items.append({"name": extracted.name, "price": round(extracted.price, 2)})
        except (ValidationError, ValueError) as exc:
            label = candidate.get("name") if isinstance(candidate, dict) else f"row {idx + 1}"
            warnings.append(f"Skipped an unreadable item ({label}): {exc}")

    return {"items": items, "warnings": warnings}
