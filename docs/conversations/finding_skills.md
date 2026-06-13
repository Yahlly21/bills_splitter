# Conversation — Finding & Installing Skills

> Saved record of the session where we researched and set up Claude Code skills to
> support the Friday Brunch Bill Splitter build. Date: 2026-06-13.

---

## 1. Task

**User:**

> Read the SPEC. Understand the laid ground I have now. Search the web for skills that
> will help me (and you) in the dev process in order to have the perfect output.
> Examples of directories I like using:
> - https://www.skillsdirectory.com/skills
> - https://www.skills.sh/

---

## 2. Understanding the laid ground

Reviewed the SPEC and scaffold. Summary of what existed:

A clean, spec-driven scaffold — rails in place, nothing implemented yet:

- **Spec** (`docs/spec/SPEC.md`): finalized. FastAPI + Pydantic backend, in-memory store
  keyed by `bill_id`, vanilla-JS frontend, Claude receipt extraction with structured
  output, two split modes (even / individual settle-and-remove), mandatory tip logic.
  Includes a time-boxed 6-step build plan.
- **Deps**: `requirements.txt` (fastapi, uvicorn, pydantic, anthropic, python-multipart,
  dotenv) + `requirements-dev.txt` (pytest, httpx, ruff).
- **Empty packages**: `app/__init__.py`, `tests/__init__.py` — no `main.py` or models yet.
- **Guardrails wired** in `.claude/`:
  - `secret_guard.py` hook (blocks reading/printing secrets) on Bash/PowerShell/Read
  - `format_python.py` + `run_tests.py` hooks on every Edit/Write
  - a `spec-compliance` subagent that checks code against the SPEC
- Sensible `.gitignore` / `.env.example` (only `ANTHROPIC_API_KEY`).

The foundation was solid; the gap was purely implementation.

---

## 3. Research findings

### Already built into the Claude Code harness (no install needed)

| Need (from SPEC) | Already-available skill/agent |
|---|---|
| Claude extraction (model id, structured output, SDK) | **`claude-api`** skill |
| Verify the app actually runs | **`run`** + **`verify`** skills |
| Code review before commit | **`code-review`**, **`review`**, **`security-review`** |
| Cleanup passes | **`simplify`** |
| Spec adherence | the project's **`spec-compliance`** subagent |
| Harness/hooks config | **`update-config`** |

### Worth adding (from skillsdirectory / skills.sh + the wider ecosystem)

Ranked by leverage for this exact project:

1. **`test-driven-development`** (obra/superpowers) — RED-GREEN-REFACTOR; ideal for the
   risky math (even-split rounding remainder, ÷N settle-and-remove, summed-not-averaged
   tips, <10% nudge).
2. **`frontend-design`** (anthropics/skills) — clean vanilla-JS/HTML UI, no build step.
3. **`webapp-testing`** (anthropics/skills) — drives a browser to test the full page flow.
4. **`systematic-debugging`** (obra/superpowers) — 4-phase root-cause process.
5. A **FastAPI expert** skill (e.g. `jezweb-fastapi`, grade A on skillsdirectory).

Skipped: document/azure/supabase/db skills — no database, no docs-generation, no cloud
SDK in this project.

---

## 4. Decisions

**User chose** (via prompt):
- Skills to add: **TDD**, **frontend-design**, **webapp-testing**
- Next step: **just install/advise skills** (don't start building yet)

Then, on the install method:

> I will rather stay minimal... copy only `frontend-design/` and `webapp-testing/` into
> `.claude/skills/` as project skills instead — fully under your control, nothing extra.
> ... I do not want any overhead. Keep things simple.

**Resolution:** install **only** `frontend-design` and `webapp-testing` as project skills
(dropped the TDD/superpowers bundle to honor "keep it simple, no overhead"). Both
anthropic skills live in the same `example-skills` marketplace bundle, which would also
pull in `skill-creator`, `mcp-builder`, `algorithmic-art`, `slack-gif-creator`, etc. —
so copying just the two folders avoids that bloat.

---

## 5. What was installed

Copied exactly these files from `anthropics/skills@main` into the repo:

```
.claude/skills/
├── frontend-design/
│   ├── SKILL.md
│   └── LICENSE.txt
└── webapp-testing/
    ├── SKILL.md
    ├── LICENSE.txt
    ├── examples/
    │   ├── console_logging.py
    │   ├── element_discovery.py
    │   └── static_html_automation.py
    └── scripts/
        └── with_server.py
```

Both have valid frontmatter:

- **frontend-design** — "Guidance for distinctive, intentional visual design when building
  new UI or reshaping an existing one."
- **webapp-testing** — "Toolkit for interacting with and testing local web applications
  using Playwright."

**Note for later:** `webapp-testing` uses Playwright, so when first used it needs
`pip install playwright` + `playwright install`. Nothing to do up front.

---

## 6. "Why don't I see them under `/skills`?"

Two reasons, both expected:

1. **Skills load at session startup.** Claude Code scans `.claude/skills/` when a session
   begins. They were added mid-session, so a **restart** is needed to pick them up.
2. **Skills aren't slash commands.** Agent Skills are *model-invoked* — Claude reads their
   descriptions and triggers them automatically when the request matches. You don't type
   `/frontend-design`; the model invokes it when relevant.

The files are in the correct location (`.claude/skills/<name>/SKILL.md`), so the install
is structurally valid — it was purely that the running session predated them. (They did
become available to the model after loading.)

---

## 7. How these map to the SPEC build plan

| SPEC build step | Skill driving it |
|---|---|
| Step 2 — Pydantic models + endpoints + **math unit tests** | `claude-api` (built-in) + TDD discipline |
| Steps 3–4 — entry/table/finalize/split/results UI | **`frontend-design`** |
| Steps 3–5 — verify full page flow + camera path | **`webapp-testing`** |
| Step 5 — Claude extraction (structured output, model id) | **`claude-api`** (built-in) |

Existing `run_tests.py` hook + `spec-compliance` subagent cover "tests run automatically"
and "matches the SPEC", so the new skills slot in without overlap.
