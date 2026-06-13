# Friday Brunch Bill Splitter

A single-organizer web app that removes the awkward end-of-meal bill dance: enter the bill
(manually or by photo via an LLM), review it as a clean editable table, then split it —
either **evenly by number of people** or **individually** (settle-and-remove) — with a
mandatory tip that flows into every total.

> Built as a spec-driven, time-boxed (~2h) project. Full spec:
> [`docs/spec/SPEC.md`](docs/spec/SPEC.md).

## Highlights

- **Two entry paths** — manual table entry, or **camera → Claude** receipt extraction with
  structured (Pydantic-validated) output and a human-in-the-loop review step.
- **Editable table** — add / edit / delete rows; a quantity field explodes into separate
  rows so shared items split cleanly.
- **Two split modes** — even split (last person absorbs rounding), or individual
  settle-and-remove with per-item ÷N sharing and a running "settled so far" log.
- **Tip-aware** — mandatory tip %, summed (never averaged) across individual batches, with a
  live overall effective tip % and a gentle nudge if it lands under 10%.
- **No database** — server-side in-memory state keyed by `bill_id`; intentionally evaporates
  on restart, matching the one-time-use design.

## Tech stack

- **Backend:** FastAPI + Pydantic
- **LLM:** Anthropic Claude API (receipt → structured items)
- **Frontend:** single `index.html` + vanilla JS (no build step), served by FastAPI
- **Deploy:** Render (free web service)

## Project layout

```
app/      FastAPI application (routes, models, in-memory store, LLM extraction)
static/   index.html + vanilla JS frontend
tests/    pytest unit tests (split/settlement math, endpoints)
docs/     spec/ and conversations/ (spec-driven design record)
.claude/  project hooks, settings, and the spec-compliance subagent
```

## Local development

```bash
# 1. Create and activate a virtualenv (Windows: py -m venv .venv && .venv\Scripts\activate)
py -m venv .venv && source .venv/Scripts/activate

# 2. Install dependencies (use requirements-dev.txt to include test/lint tooling)
pip install -r requirements-dev.txt

# 3. Provide your Anthropic key (gitignored)
cp .env.example .env   # then edit .env and set ANTHROPIC_API_KEY

# 4. Run
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000.

## Tests

```bash
pytest -q
```

## Configuration

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key for receipt extraction. Required for the camera path; set in `.env` locally and as a Render environment variable in production. |

The uploaded receipt image is used only for extraction and is **never stored**.
