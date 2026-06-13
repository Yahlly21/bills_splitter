# AGENTS.md

**Friday Brunch Bill Splitter** — single-organizer web app to enter a bill (manual or
photo→LLM) and split it evenly or individually (settle-and-remove), tip included.

- **Spec (source of truth):** `docs/spec/SPEC.md`
- **Stack:** FastAPI + Pydantic · vanilla `index.html` + JS · Anthropic Claude (extraction) · no DB (in-memory) · deploy on Render
- **Layout:** `app/` backend · `static/` frontend · `tests/` pytest · `docs/` spec & design notes
- **Run:** `uvicorn app.main:app --reload` · **Test:** `pytest -q`
- **Config:** `ANTHROPIC_API_KEY` in `.env` (gitignored; see `.env.example`)

> Keep this file short. Expand as the build progresses.
