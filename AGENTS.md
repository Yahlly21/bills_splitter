# AGENTS.md

**Friday Brunch Bill Splitter** — single-organizer web app to enter a bill (manual or
photo→LLM) and split it evenly or individually (settle-and-remove), tip included.
Spec-driven and time-boxed (~2h); the build is complete and runs end to end.

- **Spec (source of truth):** `docs/spec/SPEC.md` (status: *Finalized*) — read it before
  changing behavior; keep code and spec in sync.
- **Stack:** FastAPI + Pydantic · single-file vanilla `index.html` + JS (no build step) ·
  Anthropic Claude (real receipt extraction) · in-memory store (no DB) · deploy on Render.

## Layout

| Path | What |
|---|---|
| `app/main.py` | FastAPI routes (SPEC §5) + static serving |
| `app/models.py` | Pydantic schemas — the validation source of truth |
| `app/calc.py` | All money math (even split + settle-and-remove); unit-tested in isolation |
| `app/llm.py` | Claude receipt extraction (SPEC §8) |
| `app/store.py` | In-memory dict keyed by `bill_id` |
| `static/index.html` | Whole frontend: styles, screens, vanilla JS — responsive (mobile + web) |
| `tests/` | pytest — `test_calc.py`, `test_api.py`, `test_llm.py` |
| `docs/spec/` · `docs/conversations/` | Spec + the spec-driven design record |
| `.claude/` | Hooks, `settings.json`, and the `spec-compliance` subagent |

## Commands

- **Run:** `uvicorn app.main:app --reload` → http://127.0.0.1:8000
- **Test:** `pytest -q`
- **Lint/format:** `ruff format . && ruff check .`
- **Deps:** `requirements.txt` (runtime) · `requirements-dev.txt` (adds pytest/httpx/ruff)

## Conventions & key decisions

- **Money math lives in `app/calc.py`** — keep it framework-free and testable. Prices are
  **tax-inclusive**; round at the cent (`round2`); the even split's **last person absorbs
  the rounding remainder**; per-batch tips are **summed, never averaged**; overall tip %
  is over item subtotals only (tip excluded from the denominator).
- **Validation goes through Pydantic** (`app/models.py`): blank names and ≤0 prices are
  rejected, `qty` is exploded into separate rows server-side. Don't duplicate these rules
  in routes.
- **In-memory store is intentional** — state evaporates on restart/idle. This is a feature
  (privacy, zero infra, automatic forgetting) for a single-user one-time-use tool, not an
  oversight. No DB, no persistence.
- **The LLM path is real, not a mock.** `app/llm.py` calls Claude (`claude-opus-4-8`) with
  a one-shot worked example (`docs/receipt_example.jpg` → exact expected JSON) and
  **structured JSON-schema output**, then re-validates each row against `ExtractedItem`.
  Bad rows are dropped and surfaced as warnings; extraction never auto-commits (the
  frontend loads results into the editable table); the uploaded image is **never stored**.
- **Frontend is one file, no build step** — `static/index.html` holds styles + screens +
  vanilla JS talking to the JSON endpoints. It's responsive and **works on mobile and
  web** (`capture="environment"` for phone camera, file upload otherwise). Keep it
  dependency-free.
- **No heavyweight agent frameworks** (e.g. BMAD, superpowers) — deliberately omitted as
  overkill for an app this size.

## Hooks & secrets

- `ANTHROPIC_API_KEY` lives in `.env` (gitignored; see `.env.example`) locally and as a
  Render env var in production. Required for the camera path only.
- The **secret-guard hook** blocks reading/printing/committing `.env` — don't try to route
  around it. On edits to `app/`/`tests/`, hooks auto-run **ruff format** and **pytest**;
  a failing test is reported back, so keep the suite green.
- The LLM extraction path is **excluded from pytest** (needs a live key) — verify it by
  running the app manually.
