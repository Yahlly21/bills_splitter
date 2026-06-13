"""Unit tests for the extraction parsing logic (SPEC §8 / #3.1).

The Anthropic client is mocked, so these run without an API key and verify the
drop-and-surface and graceful-failure behavior rather than the model itself.
"""

import json

import pytest

from app import llm


class _Block:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _Response:
    def __init__(self, text: str):
        self.content = [_Block(text)]


@pytest.fixture
def fake_anthropic(monkeypatch):
    """Patch llm.anthropic.Anthropic to return a client with a canned response."""

    def _install(response_text: str):
        from unittest.mock import MagicMock

        client = MagicMock()
        client.messages.create.return_value = _Response(response_text)
        monkeypatch.setattr(llm.anthropic, "Anthropic", lambda *a, **k: client)

    return _install


def test_valid_extraction(fake_anthropic):
    fake_anthropic(
        json.dumps(
            {
                "items": [
                    {"name": "Latte", "price": 4.5},
                    {"name": "Toast", "price": 6},
                ]
            }
        )
    )
    result = llm.extract_items(b"fake-image-bytes")
    assert result["warnings"] == []
    assert result["items"] == [
        {"name": "Latte", "price": 4.5},
        {"name": "Toast", "price": 6.0},
    ]


def test_invalid_rows_dropped_and_surfaced(fake_anthropic):
    fake_anthropic(
        json.dumps(
            {
                "items": [
                    {"name": "Eggs", "price": 12.0},  # valid
                    {"name": "Free sample", "price": 0},  # non-positive → dropped
                    {"price": 5.0},  # missing name → dropped
                ]
            }
        )
    )
    result = llm.extract_items(b"img")
    assert result["items"] == [{"name": "Eggs", "price": 12.0}]
    assert len(result["warnings"]) == 2


def test_malformed_json_raises_runtimeerror(fake_anthropic):
    fake_anthropic("this is not json at all")
    with pytest.raises(RuntimeError):
        llm.extract_items(b"img")


def test_missing_items_key_raises_runtimeerror(fake_anthropic):
    fake_anthropic(json.dumps({"rows": []}))
    with pytest.raises(RuntimeError):
        llm.extract_items(b"img")
