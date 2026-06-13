# Implement: Full Build & Spec-Compliance Fixes

**Session:** June 13, 2026  
**Scope:** End-to-end implementation of the Friday Brunch Bill Splitter per SPEC, with spec-compliance review and fixes.

## What Was Built

**Backend (`app/`)**
- `models.py` — Pydantic schemas for `Item`, `SettledRecord`, `Bill`, `ExtractedBill`, all request models, with validators enforcing SPEC §9 edge cases
- `calc.py` — Core money math: even split (last-person rounding), settle-and-remove (÷N with epsilon drop), tip summing (not averaging), overall effective tip % 
- `store.py` — In-memory bill store keyed by `bill_id`
- `llm.py` — Claude extraction via one-shot example + structured output, per-row validation with drop-and-surface for invalid rows
- `main.py` — All 7 SPEC §5 endpoints, finalize gate, static serving, health check

**Frontend (`static/index.html`)**
- Single-file vanilla JS, no build step
- 6 screens: entry → camera/manual → editable table → finalize → split method choice → result (even or individual)
- **Diner-check vernacular:** perforated receipt edge, monospaced tabular numbers, dotted leader lines
- Palette: warm paper `#F4F1E6`, espresso `#211A12`, tomato-jam accent `#DB3B2B`

**Tests (`tests/`)**
- `test_calc.py` — 11 unit tests for money math (rounding, tip summing, low-tip nudge)
- `test_api.py` — 12 endpoint tests covering CRUD, qty explosion, finalize gate, settle flow
- `test_llm.py` — 4 mocked LLM tests for extraction parsing, drop-and-surface, graceful failure

**Status:** 29 tests passing, ruff clean, real `uvicorn` server boots and serves all endpoints.

## Spec-Compliance Review & Fixes

Ran a spec-compliance subagent against `docs/spec/SPEC.md` and fixed three findings:

### 1. Server-side finalize gate (SPEC §2, §6.4)
**Finding:** `split/even` and `settle` endpoints didn't check `bill.finalized` — clients could split without finalizing.  
**Fix:** Added gate to both endpoints; returns 400 if `not bill.finalized`.  
**Tests added:** `test_split_requires_finalize()`, `test_settle_requires_finalize()`

### 2. Original subtotal tracking (SPEC §7)
**Finding:** Overall tip % was computed using reconstructed subtotal (paid + remaining) instead of the original item prices, causing sub-cent drift in rare splits.  
**Fix:** Added `bill.original_subtotal` field, set when items are saved, use it as the denominator for overall tip %.  
**Fallback:** Tests that build bills in-memory still work (empty `original_subtotal` falls back to reconstructed sum).

### 3. No test coverage for LLM extraction path
**Finding:** `extract_items()` parsing, drop-and-surface, and graceful failure had zero test coverage.  
**Fix:** Added `test_llm.py` with mocked Anthropic client covering: valid parse, invalid-rows-dropped, malformed JSON error.

## Environment Setup

```bash
# Copy the example env and fill in your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# .env is gitignored; .env.example remains as a reference
```

## Build & Test Commands

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Run all tests
pytest -q

# Run specific test suites
pytest tests/test_calc.py -q     # Money math
pytest tests/test_api.py -q      # Endpoints
pytest tests/test_llm.py -q      # Extraction parsing

# Start the dev server
uvicorn app.main:app --reload
# Navigate to http://localhost:8000
```

## Implementation Notes

- **LLM extraction:** Uses `claude-opus-4-8` with structured output via `output_config.format` json-schema. One-shot prompt embeds `receipt_example.jpg` as base64 + exact expected JSON. Image never stored.
- **Graceful failure:** If extraction fails (malformed response, validation error), `/extract` returns 422 with warnings; frontend offers manual entry fallback.
- **In-memory state:** Bills evaporate on restart — intentional for privacy and "one-time use" UX.
- **Browser testing:** Full HTTP flow covered by TestClient tests; browser visual check is manual (Playwright install blocked on Python 3.9 greenlet dependency).

## What's Ready

- ✅ All 7 endpoints working, spec-compliant
- ✅ Frontend covering all 6 screens with diner-check design
- ✅ Unit test coverage for calculations and endpoints
- ✅ Mocked LLM tests for extraction logic
- ✅ Real `uvicorn` server boots and serves static + API

## Next Steps (Optional)

- Manual browser verification of camera/LLM extraction path (requires live `ANTHROPIC_API_KEY`)
- Deploy to Render (SPEC §3, build step 6)
