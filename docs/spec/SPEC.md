# SPEC — Friday Brunch Bill Splitter

> Status: **Finalized** · Last updated: 2026-06-13

## 1. Problem & goal
Every Friday a group meets for brunch, and the end of the meal turns into an awkward
dance: who ordered what, and how do we fairly add the tip? This app removes that
friction. A single organizer drives the whole process on one device, from entering the
bill to telling each person exactly what they owe (tip included).

## 2. Scope

**In scope**
- Single-user, single-session, **one-time use**. No accounts, no history.
- Two ways to enter a bill: **Manual** and **Camera (LLM extraction)**.
- Editable, table-style bill with add / edit / delete / qty-explode.
- Finalize gate → choose split method → results.
- Two split methods: **evenly by # of people** and **individual settle-and-remove**.
- Mandatory **Tip %** (0 allowed), applied to all totals.

**Out of scope (explicit non-goals)**
- Persistence of past bills, multi-user / real-time collaboration, payment processing,
  authentication, and a separate tax field (item prices are taken as **tax-inclusive**).

## 3. Tech stack
- **Backend:** FastAPI + Pydantic (schemas / validation).
- **LLM:** Anthropic Claude API for receipt → structured items (exact model id / SDK
  details pulled from the current reference at build time).
- **Frontend:** Single `index.html` + vanilla JS (no build step), served by FastAPI;
  talks to JSON endpoints.
- **State:** In-memory dict on the server keyed by `bill_id` (**no DB**). Evaporates on
  restart / idle — intentional, and matches the "one-time use" requirement.
- **Deploy:** Render (free web service), `requirements.txt` + start command;
  `ANTHROPIC_API_KEY` provided as an environment variable.

> **Deliberate trade-off:** in-memory state is lost on server restart and does not scale
> past one process. For a single-user, one-time-use tool this is a *feature* (privacy,
> zero infra, automatic forgetting of old bills), not an oversight.

## 4. Data model (Pydantic)

```text
Item:
  id: str
  name: str
  price: float            # tax-inclusive, full price of the row
  remaining: float        # = price initially; reduced as it is settled
  # qty is an entry-time convenience only and is exploded into separate Item rows

SettledRecord (kept for the session, individual mode only):
  name: str | None
  items: list[{ name, amount }]   # what this batch covered
  subtotal: float
  tip_pct: float                  # this batch's tip
  tip_amount: float
  total: float

Bill:
  id: str
  items: list[Item]               # current / remaining items
  tip_pct: float = 0              # used by the 'even' split mode
  finalized: bool = False
  settled: list[SettledRecord] = []   # audit trail for individual mode
```

## 5. API (FastAPI, JSON)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/bills` | Create empty bill → returns `bill_id` |
| GET  | `/api/bills/{id}` | Fetch current bill state |
| PUT  | `/api/bills/{id}/items` | Replace full items list (table save) |
| POST | `/api/bills/{id}/extract` | Multipart image → Claude → returns extracted items (does **not** auto-commit; frontend loads them into the editable table) |
| POST | `/api/bills/{id}/finalize` | Mark finalized |
| POST | `/api/bills/{id}/split/even` | Body `{ people: N, tip_pct }` → per-person amount |
| POST | `/api/bills/{id}/settle` | Body `{ name?, claims[], tip_pct }` → records the batch, reduces item `remaining`, drops items at 0, and returns the full updated picture |

**`/settle` response shape:**
```json
{
  "settlement": { "name": "Dana", "subtotal": 0, "tip_amount": 0, "total": 0 },
  "remaining_items": [],
  "settled": [],
  "totals": {
    "paid_so_far": 0,
    "remaining_amount": 0,
    "total_tip_amount": 0,
    "overall_tip_pct": 0
  }
}
```

## 6. Page flow (frontend)

1. **Entry** — two large buttons: *Enter manually* / *Use camera*.
2. **Camera** — file / photo input → POST `/extract` → spinner → table pre-filled
   (human-in-the-loop review).
3. **Table** — columns: *Name · Price · Qty · 🗑*; **+** adds a row; on **Continue**,
   any row with qty > 1 **explodes into separate rows**; saved via PUT.
4. **Finalize** — "Is this bill finalized?" with **Back** / **Continue to split**.
5. **Split method** — radio: *Evenly by # of people* (number input) or *Individually*;
   **Tip %** field is **required** (enter 0 for no tip).
6. **Results** — branch by method:

### 6.5 Results — Even split
A single number: `Σ(prices) × (1 + tip%) ÷ N`. Rounded to cents; the **last person
absorbs any rounding remainder**.

### 6.6 Results — Individual (settle-and-remove)
Three live regions, so the organizer always sees the full state:

- **Remaining** — table of unpaid items with running balances.
- **Settled so far** — running log: each entry shows **who** (name, if given), the items
  they covered, and their total incl. tip. *(Requirement #1 — full awareness of what is
  paid, by whom, and what is left.)*
- **Batch builder** — checkboxes + per-row **÷N** control + **Tip %** + optional **name**
  → **Mark paid**. Marking paid reduces each claimed item's `remaining` and removes any
  item whose balance hits 0.

When the remaining table empties → **"All settled 🎉"** summary showing:
- Grand total paid.
- **Summed tip across all batches** — different per-batch tips are **added up**, never
  averaged. *(Requirement #2.)*
- **Overall effective tip %** = `total_tip_amount / Σ(item prices) × 100`, tracked live.
  **If overall tip % < 10%**, show a gentle nudge, e.g.
  *"Heads up — the table tipped 7% overall; standard is ~15–20%."* *(Requirement #2.1.)*

## 7. Calculations
- Tip is a single % applied to the relevant subtotal (full bill, or a settled batch).
- **Even split:** `(Σ price × (1 + tip)) / N`, rounded to cents; last person absorbs the
  rounding remainder.
- **Settlement total:** `Σ claimed × (1 + tip)`.
- **Shared item ÷N:** claimed amount = `price / N`; item `remaining -= claimed`; item is
  removed when `remaining <= 0.005`.
- **Total tip (individual):** `total_tip_amount = Σ (each batch's tip_amount)` — per-batch
  tips are summed, never averaged.
- **Overall tip %:** `total_tip_amount / Σ(item prices) × 100`, computed over item
  subtotals only (tip excluded from the denominator), evaluated against the 10% threshold
  at completion.

## 8. LLM extraction
- **One-shot prompt:** the prompt includes an **example receipt** as a worked example —
  sample input (receipt) paired with the exact expected JSON output — so Claude has a
  concrete pattern to follow. *(Requirement #3.)*
  - A clearly marked placeholder in the prompt template holds the example receipt and its
    ideal JSON output; this is filled in during the LLM build step.
- **Structured output:** *(Requirement #3.1)* extraction is constrained to a schema using
  the Anthropic SDK's structured-output mechanism (tool / response-format style),
  validated server-side against a Pydantic `ExtractedBill` model. Any item that fails
  validation is dropped and surfaced to the user rather than crashing the request. This
  guarantees the LLM response maps cleanly onto the `Item` schema before it reaches the
  table.
- Prompt intent: *"Extract every line item from this receipt. Return a JSON array of
  `{name, price}`; ignore subtotal / tax / total / tip rows; prices as numbers."*
- The uploaded image is **discarded after extraction** (never stored).

## 9. Edge cases
- Empty table is blocked from finalizing.
- Blank tip → validation error (the user must explicitly enter 0).
- `N >= 1` enforced for even split.
- Negative or zero prices rejected.
- LLM returns malformed JSON / fails validation → graceful error; fall back to manual
  entry.
- Float rounding handled at display (2 dp).
- Mixed tips across batches are preserved individually and summed for the total.
- Overall tip % is computed over item subtotals only (tip excluded from denominator).
- Empty `settled` list and empty items cannot both occur at completion (guarded).

## 10. Build plan (~2h, time-boxed)
1. **0:15** — Repo, folders, `requirements.txt`, FastAPI skeleton, in-memory store,
   health check, run locally.
2. **0:35** — Pydantic models + core endpoints (create / get / items / even / settle)
   + unit test for the math.
3. **0:30** — Frontend: entry, table (+ / edit / delete / qty-explode), finalize.
4. **0:20** — Split method + both results screens (incl. settled log + tip tracking).
5. **0:15** — Claude extraction endpoint (structured output + one-shot example) and wire
   the camera path.
6. **0:05** — Deploy to Render, smoke test.
