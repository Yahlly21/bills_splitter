# Friday Brunch Bill Splitter

A single-organizer web app that removes the awkward end-of-meal bill dance: one person enters
the bill — **manually or by snapping a photo of the receipt** — reviews it as a clean editable
table, then splits it **evenly by number of people** or **individually** (settle-and-remove),
with a mandatory tip that flows into every total. Works on **mobile and desktop**.

> Built as a spec-driven, time-boxed (~2 h) project for an AI-startup take-home. The interesting
> part is what was deliberately *left out*. Full spec: [`docs/spec/SPEC.md`](docs/spec/SPEC.md);
> the complete AI design/build transcripts live in [`docs/conversations/`](docs/conversations/).

## Live demo

Deployed on **Render's free tier** — deploying is a ~1-minute setup (connect the GitHub repo,
add one env var, ship; no Dockerfile needed). The free instance spins down after ~15 minutes
idle, so the **first request after a quiet spell takes ~30–60 s to wake**, then it's snappy.
That cold-start cost is a non-issue here and actually reinforces the one-time-use design.

> _Set your deployed URL here once live, e.g._ `https://bills-splitter.onrender.com`

## Highlights

- **Two entry paths, one table** — type rows manually, or **snap the receipt → Claude extracts
  the line items**, both landing in the same editable, human-reviewable table.
- **The camera path is a real LLM call, not a mock** — live Anthropic Claude vision request with
  structured, schema-validated output (see [below](#receipt-extraction-real-llm-not-a-mock)).
- **Editable table** — add / edit / delete rows; a quantity field explodes into separate rows so
  shared items split cleanly.
- **Two split modes** — even split (last person absorbs the rounding remainder), or individual
  **settle-and-remove** with per-item ÷N sharing and a running "settled so far" log.
- **Tip-aware** — mandatory tip %, **summed (never averaged)** across individual batches, with a
  live overall effective tip % and a gentle nudge if it lands under 10 %.
- **No database** — server-side in-memory state keyed by `bill_id`; intentionally evaporates on
  restart, matching the one-time-use design.
- **Diner-check design** — a single hand-tuned `index.html`: perforated receipt edge, monospaced
  tabular numbers, warm-paper palette. Responsive for phone and desktop.

## Key product decisions

The brief was deliberately simple; the signal being tested is scope discipline and product
judgment. These calls (made across the design conversations and folded into the spec) are the core:

| Decision | Choice | Why |
|---|---|---|
| Persistence | **No database** — in-memory dict keyed by `bill_id` | Single-user, one-time-use; a DB is pure overhead and free-tier disks are ephemeral anyway. Privacy + auto-forgetting are *features*. |
| Users | One organizer, one device, one session | Keeps the whole flow on the phone settling the bill; no auth, no sync, no shared links. |
| Bill entry | Manual **and** camera/LLM, converging on one editable table | Camera targets the slowest step (typing items); manual is the always-works fallback. |
| Tax | None separate — **prices are tax-inclusive** | One less field; receipts already print tax-inclusive line prices. |
| Tip | **Mandatory** Tip % (0 allowed), applied to all totals | Forces an explicit choice — no silently-forgotten tip. |
| Shared items | A single item can be split **÷N** via a remaining-balance mechanic | An item leaves the table only when its balance hits 0, so partial shares reconcile exactly. |
| Even-split rounding | **Last person absorbs the remainder** | Shares always sum back to the exact grand total to the cent. |
| Mixed tips (individual) | **Summed, never averaged**; overall effective % tracked | Different batches can tip differently; a <10 % overall result triggers a gentle nudge. |
| Frontend | Single `index.html` + vanilla JS, **no build step** | Fastest path to a clean, finished, mobile-friendly UI; nothing to compile or bundle. |
| Deploy | **Render** free web service | Genuine persistent free tier, no credit card, git-push deploy; spin-down reinforces one-time use. |

A fuller decision ledger lives at the bottom of
[`docs/conversations/spec-design-conversation.md`](docs/conversations/spec-design-conversation.md).

## How the bill is split

**Even split** — `Σ(prices) × (1 + tip%) ÷ N`, rounded to cents, with the last person absorbing
any rounding remainder so the per-person amounts always reconcile to the grand total.

**Individual (settle-and-remove)** — the organizer always sees three live regions:

- **Remaining** — unpaid items with running balances.
- **Settled so far** — a log of each batch: who paid (optional name), what items, and the total
  incl. tip.
- **Batch builder** — check items, optionally ÷N to share a row, set this batch's tip %, add an
  optional name, **Mark paid**. Each claim reduces the item's balance; items at 0 drop off.

When the table empties → an **"All settled 🎉"** summary: grand total paid, **summed** tip across
all batches, and the **overall effective tip %** (`total_tip / Σ item prices × 100`) — with a
nudge if it came in under 10 %.

## Receipt extraction (real LLM, not a mock)

The camera path issues a **live Anthropic Claude** request (model `claude-opus-4-8`) — verified
end-to-end against the example receipt (see [`docs/conversations/codex_tests.md`](docs/conversations/codex_tests.md)).
It is implemented in [`app/llm.py`](app/llm.py) and built around three deliberate choices:

- **One-shot worked example** — the prompt embeds [`docs/receipt_example.jpg`](docs/receipt_example.jpg)
  paired with its exact expected JSON, so Claude has a concrete pattern to follow (including a
  multilingual, Hebrew receipt).
- **Structured, validated output** — the response is constrained to a JSON schema, then every row
  is re-validated server-side against a Pydantic model. Rows that fail are **dropped and surfaced
  as warnings** rather than crashing the request; a malformed response falls back to manual entry.
- **Final, per-unit rows** — the LLM splits quantity lines (e.g. `2 × 6.60`) into separate
  per-unit rows so results drop straight into the table with no further explosion. Subtotal / tax /
  total / payment lines are ignored.

Extraction never auto-commits — results populate the editable table for **human-in-the-loop**
review. The uploaded image is used only for the call and is **never stored**.

## Tech stack & architecture

- **Backend:** FastAPI + Pydantic (schemas are the single source of truth for validation).
- **LLM:** Anthropic Claude API (receipt → structured items).
- **Frontend:** single `index.html` + vanilla JS (no build step), served by FastAPI.
- **State:** in-memory dict keyed by `bill_id` — **no DB**. Deliberate trade-off: state is lost on
  restart and doesn't scale past one process, which for a single-user one-time-use tool is a
  feature (privacy, zero infra), not an oversight.
- **Deploy:** Render free web service; `ANTHROPIC_API_KEY` provided as an environment variable.

```
app/
  main.py     FastAPI routes (7 JSON endpoints) + static serving + health check
  models.py   Pydantic schemas — validation source of truth (blank names / ≤0 prices rejected)
  calc.py     All money math (even split + settle-and-remove); framework-free, unit-tested
  llm.py      Claude receipt extraction (one-shot example + schema-validated output)
  store.py    In-memory bill store keyed by bill_id
static/
  index.html  Whole frontend: styles + screens + vanilla JS, responsive (mobile + web)
tests/        pytest — calc math, API endpoints, mocked LLM parsing
docs/         spec/ (source of truth) + conversations/ (the spec-driven design record)
.claude/      hooks, settings, and the spec-compliance subagent
```

## How this was built (the AI story)

The AI sophistication was put into **how the app was built**, not crammed into the app:

- **Spec-driven** — `docs/spec/SPEC.md` was finalized and committed *before* any code; the full
  design and build conversations are preserved verbatim under `docs/conversations/`.
- **Guardrail hooks** (`.claude/`) — a **secret-guard** that blocks reading/printing/committing
  `.env`, plus **ruff auto-format** and **pytest auto-run** on every edit (a failing test is
  reported straight back).
- **`spec-compliance` subagent** — reviews the implementation against the spec; its first pass
  caught three real gaps that were then fixed (see below).
- **Project skills, kept minimal** — only `frontend-design` and `webapp-testing` were installed.
  Heavyweight agent frameworks (e.g. BMAD, superpowers/TDD bundles) were **intentionally skipped
  as overkill** for an app this size — the goal was a finished, clean build with no overhead.

### Notable fixes & refinements

- **Server-side finalize gate** — `split/even` and `settle` now reject requests on a non-finalized
  bill (clients previously could split without finalizing).
- **Accurate overall tip %** — switched the denominator to the original item subtotal captured at
  save time, fixing sub-cent drift as items were removed during settlement.
- **LLM test coverage** — added mocked tests for the extraction path (valid parse, invalid rows
  dropped, malformed JSON handled gracefully).
- **Sharper extraction prompt** — added receipt-anatomy guidance and a comprehensive ignore list so
  Claude reliably skips store info / totals / payment lines across receipt formats.

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

Then open http://127.0.0.1:8000. On Windows without `python`/`pip` on PATH, use the launcher:
`py -m pip ...`, `py -m pytest -q`, `py -m uvicorn app.main:app --reload`.

## Tests

```bash
pytest -q     # 29 tests: split/settlement math, endpoints, mocked LLM parsing
```

The live LLM extraction path is not exercised by pytest (it needs a real API key) — it's verified
by running the app manually against `docs/receipt_example.jpg`.

## Deployment (Render)

A ~1-minute setup, no Dockerfile required:

1. Create a **New Web Service** on Render from this GitHub repo.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add the `ANTHROPIC_API_KEY` environment variable.

Render auto-detects the Python build and gives you a public URL. (Considered Railway and a
deploy-agnostic Dockerfile path — both rejected as either no-longer-free or unnecessary overhead
for this size; see [`docs/conversations/where_to_deploy.md`](docs/conversations/where_to_deploy.md).)

## Configuration

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key for receipt extraction. Required for the camera path; set in `.env` locally and as a Render environment variable in production. |

The uploaded receipt image is used only for extraction and is **never stored**.
