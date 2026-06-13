# Conversation — Docs Cleanup (AGENTS.md + README)

> Project: Friday Brunch Bill Splitter
> Date: 2026-06-13
> Purpose: Record of the post-build documentation pass — expanding `AGENTS.md` and rewriting
> `README.md` to reflect the finished app, then finalizing the live URL and headline.

---

## 1. Update AGENTS.md

**User:**

> I want to update the AGENTS.md. Read the full context of the project first — from the spec
> to the app itself. Go over the docs and understand the key decisions I made. Also note:
> intentionally haven't used advanced methods like BMAD and superpowers (overkill for this
> app); the LLM part is functioning and not a mock; works for mobile and web.

**Assistant:** Read the full context first — `docs/spec/SPEC.md`, all of `app/` (`main.py`,
`models.py`, `calc.py`, `llm.py`, `store.py`), `static/index.html`, the tests, `.claude/` hooks
and settings, and the deps/config files. Verified the mobile camera support
(`capture="environment"` in `index.html`) and the real Claude model id (`claude-opus-4-8`).

Then rewrote the previously-stub `AGENTS.md` into a dense agent guide:
- A **layout table** naming each file and its responsibility.
- **Commands** (run / test / lint / deps), adding the missing ruff step.
- **Conventions & key decisions** — money math isolated in `calc.py`, Pydantic as the single
  validation point, in-memory store as a deliberate feature, the LLM path being **real, not a
  mock**, single-file responsive frontend (mobile + web), and the deliberate omission of
  heavyweight agent frameworks (BMAD, superpowers).
- **Hooks & secrets** — secret-guard, ruff/pytest on edit, LLM path excluded from pytest.

All three flagged points were captured explicitly.

**User:** `Commit push it (short commit message)`

**Assistant:** Committed and pushed `AGENTS.md` (`44848ac` — "Expand AGENTS.md for completed
build").

---

## 2. Rewrite README.md

**User:**

> Now do the same for the README. Note the 3 points from before + that it's deployed to
> Render's free tier so setup takes ~1 min. Important to write that the LLM is not a mock!
> Write all important decisions I made in the spec, conversations, bug fixing, and so on.
> This README is very important.

**Assistant:** Mined the full decision history by reading all eight conversation logs
(`spec-design-conversation`, `ground_laying`, `implement`, `enhance_llm_prompt`,
`where_to_deploy`, `codex_tests`, `finding_skills`, `bad_start`), confirmed the test suite
(**29 passing**), and checked there was no deploy config file (Render is configured via its
dashboard).

Rewrote `README.md` as an interview-grade document:
- New **Live demo** section (Render free tier, ~1-min setup, ~30–60 s cold start).
- **Highlights** and a dedicated **"Receipt extraction (real LLM, not a mock)"** section.
- A **Key product decisions** table (no-DB, tax-inclusive prices, mandatory tip, ÷N sharing,
  last-person rounding, tips summed-not-averaged + <10% nudge, single-file frontend, Render).
- **How the bill is split** (even + settle-and-remove math).
- **Tech stack & architecture** with the file-tree layout.
- **How this was built (the AI story)** — spec-first, guardrail hooks, `spec-compliance`
  subagent, minimal skills, and the deliberate skip of BMAD/superpowers.
- **Notable fixes** — finalize gate, overall-tip-% denominator drift, added LLM test coverage,
  sharpened extraction prompt.
- **Local development**, **Tests**, **Deployment (Render)**, **Configuration**.

The three required points (LLM not a mock, mobile + web, no BMAD/superpowers) and the Render
~1-min deploy detail were all included.

---

## 3. Clarifying the local run command

**User:** `py -m uvicorn app.main:app --reload isn't it the command needed for the local
deployment?`

**Assistant:** Confirmed `py -m uvicorn app.main:app --reload` is the command to run it locally
on this Windows machine — equivalent to bare `uvicorn app.main:app --reload`, with the `py -m`
prefix needed because `uvicorn`/`python`/`pip` aren't on PATH (only the `py` launcher resolves).
Clarified that this is the *local dev* command; the *Render* start command is
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`. The README already covered both (portable
form as the headline + a `py -m` note for Windows), and offered to flip which is primary.

**User:** `no, it is all good. Commit and push the new README`

**Assistant:** Committed and pushed `README.md` (`4fc8fd6` — "Rewrite README for completed build").

---

## 4. Adding the live URL

**User:** Provided the live link — `https://bills-splitter.onrender.com` — and asked to put it
in the README.

**Assistant:** Replaced the placeholder in the *Live demo* section with the real link
(**▶ Live app: https://bills-splitter.onrender.com**). Committed and pushed (`3601380` — "Add
live Render URL to README").

---

## 5. Headline change

**User:** `"Friday Brunch Bill Splitter" -> Cognitory Friday Brunch Bill Splitter`

**Assistant:** Updated the README H1 to **Cognitory Friday Brunch Bill Splitter**. Committed and
pushed (`f6e4f66` — "Update README headline").

---

## Commit trail

| Hash | Summary |
|---|---|
| `44848ac` | Expand AGENTS.md for completed build |
| `4fc8fd6` | Rewrite README for completed build |
| `3601380` | Add live Render URL to README |
| `f6e4f66` | Update README headline |
