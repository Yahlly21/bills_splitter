# Brainstorm & Planning — Friday Brunch Bill Splitter

> Working session: shaping a home-assignment idea using a spec-driven approach.
> Roles: User (interview candidate) + Claude (acting as senior PM / advisor).

---

## User

I am interviewing for a position in an AI startup. I got a home assignment. I want to use this chat to brainstorm and polish my idea.

Act like a professional advisor and a senior product manager and help me shape it.

Here is the task:

> Every Friday you meet a few of your friends at a coffee shop for brunch. When the meal is done and everyone's ready to go home, there's often an awkward dance around the bill. Who ordered what? How do we split the tip?
> Build a web app that solves this problem. Make sure to spend less than two hours; when you're done, send us:
> 1. A link to the app
> 2. The codebase + commit history
> 3. Transcript of your chat(s) with the AI
> We are NOT testing for perfect prompts. :)

I want to take a spec-driven development approach and plan it intensively before starting. Let's start.

---

## Claude

Good assignment — it's deliberately simple on the surface, and the interesting part is what you choose *not* to build. Before we write any spec, here's the lens I'd use, then I want to lock three decisions that determine everything downstream.

**What they're really testing.** Not bill-splitting math — that's trivial. With a 2-hour ceiling plus a request for your AI transcript and commit history, the signal they're reading is: can you scope ruthlessly, is your product judgment good enough to solve the *real* friction, and can you drive an AI build cleanly. The two-hour limit *is* the test. Anyone can pile on features; the impressive submission is a tight, finished, obviously-fair product with a clean commit trail.

**The insight to anchor the spec.** The "awkward dance" isn't a math problem, it's a speed-and-fairness UX problem. Equal splits feel unfair when one person had a steak and another had a flat white, and nobody wants to itemize out loud. So the product wins on exactly two axes: *fast input* and *output that's instantly, visibly fair.* Every scope call should serve those two and nothing else.

**Where AI fits, if at all.** That same insight tells you the one place AI earns its keep: the slowest, most annoying step is typing in every line item, so "snap the receipt → auto-extract items" is the single AI feature that targets the actual pain. It's genuinely feasible now with one vision-model call returning structured items — but it adds real risk (image handling, parse reliability, key management) and eats your clock. My instinct is to build a rock-solid manual core first and treat receipt-scan as a timeboxed stretch you only touch if the core is done early. Even if you don't finish it, *articulating why it's the right AI bet* in your spec scores product points at an AI startup.

A couple of recommendations I'll bake into the spec once we align: keep it a backend-free React SPA deployed to Vercel/Netlify (fastest path to a live link with clean commits), distribute tip/tax *proportionally* to each person's subtotal rather than evenly (that's the "fair" that kills the awkwardness), and — if you want sharing without a backend — encode the whole bill in the URL so a link "just works."

Three forks decide the spec and your time plan. Let's lock them:

1. **How ambitious should the AI angle be?** (It's an AI startup, but the 2-hr clock is brutal.) — Manual MVP only / Manual MVP + receipt-scan as timeboxed stretch / AI-first: receipt-scan is the headline
2. **Who actually uses it at the table?** — One phone, one person drives it / Shareable link, everyone on own phone
3. **How are you planning to build it?** — AI coding agent (Claude Code / Cursor) / AI app builder (Lovable / Bolt / v0) / Hand-code, I'm comfortable

---

## User

**Q: How ambitious should the AI angle be?**
A: I will want to use AI in the dev process more than in the app. Skills, sub-agents and so on. I will write the code in Claude Code.

**Q: Who actually uses it at the table?**
A: One phone, one person drives it.

**Q: How are you planning to build it?**
A: AI coding agent (Claude Code / Cursor).

---

## Claude

Those three answers lock the scope nicely, and your AI call is the smart one. Putting the AI sophistication in *how you build* rather than cramming a flaky OCR feature into the app means the thing you ship is small, finished, and fair — while your transcript and commit history carry the "I can drive an AI build" signal. That's exactly the split of effort the assignment rewards. So: a backend-free, single-screen, manual-entry SPA, built spec-first in Claude Code with clean incremental commits.

Here's the full spec. Read it as a draft to react to — I've flagged the few judgment calls at the end.

---

### Spec — "Divvy" (working name): Friday Brunch Bill Splitter

**Problem & context.** One person settles a group brunch bill on their phone and needs to tell everyone what they owe — fairly by what they ordered, and fast, without a line-by-line negotiation at the table. The operator is reading off a paper bill and wants the answer in under a minute.

**Goals (the demo succeeds if all are true).** Enter a realistic bill (≈4 people, ≈10 items) in under 60 seconds; assign shared items in a tap or two; produce per-person totals that are provably fair; numbers always reconcile to the bill total to the cent; clean, mobile, live at a URL.

**Non-goals (deliberately out — this is where judgment shows).** No accounts/auth, no backend or database, no payments or payment links, no multi-device sync or shared links, no receipt OCR, no multi-currency, no saved history, no uneven custom splitting of a shared item. Shared item = equal split among its assignees, full stop.

**The fairness model (the heart of it).**
- Person subtotal = sum over their items of `price ÷ (number of people sharing that item)`.
- Tip and tax are allocated **proportionally** to subtotal: `personShare = (personSubtotal ÷ billSubtotal) × (tip + tax)`.
- Person total = subtotal + proportional tip + proportional tax.
- Rounding: round each person to cents, then drop any leftover cent onto the largest payer so the sum equals the exact grand total.

Proportional, not equal, is the whole point — the person who had a coffee shouldn't pay equal tip on someone's steak. That's the awkwardness you're removing.

**Core flow (single screen, stacked sections).** Add people → add items (name + price, tap person-chips to assign) → set tip (15/18/20/custom) and tax ($ or %) → sticky summary footer shows live per-person totals → expand for the full per-person breakdown.

**Requirements, prioritized.**

- **P0 — must work:** add/remove people; add/edit/remove items with price; assign each item to ≥1 person (equal split when shared); enter tip (% or $) and tax ($ or %); compute subtotals + proportional tip/tax + totals; totals reconcile with rounding handled; per-person summary; mobile-responsive; deployed.
- **P1 — makes it feel finished:** tip quick-buttons; live-updating totals; "unassigned items" warning so nothing slips; clean empty state; localStorage so a refresh doesn't wipe the bill.
- **P2 — only if ahead:** copy summary as text (operator pastes it into the group chat — fits single-operator perfectly); uneven shared-item split.

**Data model (minimal).**
```
Person { id, name }
Item   { id, name, price, assignedTo: personId[] }
Bill   { people[], items[], tip:{mode:'pct'|'amt', value}, tax:{mode,value} }
// derived: per-person subtotal/tipShare/taxShare/total, grandTotal, unassigned[]
```
All in React state, mirrored to localStorage.

**Edge cases to handle explicitly.** Item assigned to nobody (warn, don't drop); person with zero items (total $0, not an error); tip/tax as % vs $; rounding remainder; removing a person who's on items (pull them off those items); empty initial state.

**Stack.** React + Vite + TypeScript + Tailwind. No backend. Deploy to Vercel or Netlify. Pure client-side math, so it's trivially unit-testable.

**Claude Code workflow — your actual AI story.** This is what the transcript and commits should showcase:
- Commit `SPEC.md` *first* — proves spec-driven discipline before any code.
- Add a `CLAUDE.md` with conventions (stack, the fairness rules above, commit-message style) so the agent stays consistent across the session.
- Use a subagent or skill for something real, e.g. a small QA/"fairness-checker" pass that verifies totals reconcile, or a planning subagent that breaks the spec into the commit slices below.
- Incremental, scoped commits: scaffold → data model → people → items+assignment → tip/tax+math → summary → polish → deploy. Small and meaningful — the history *is* the evidence.
- Have the agent write 2–3 unit tests for the fairness math (proportional split + rounding remainder). Cheap, and it signals rigor.

**Time budget (2 hr).**
- 0:00–0:15 — finalize spec, scaffold Vite, deploy the empty shell so the live URL works *now* (deploy is never what bites you at minute 115).
- 0:15–1:15 — P0 core, commit per slice.
- 1:15–1:40 — P1 polish.
- 1:40–1:55 — math tests, README, final deploy.
- 1:55–2:00 — buffer + write a 3-line "what I'd build next: receipt OCR" note.

---

**Three judgment calls for sign-off:** dropped receipt-scan to a one-line "future work" mention rather than a stretch (keeps you focused — agree?); put the leftover rounding cent on the largest payer (alternative: on the operator, since they're paying anyway — your call); kept localStorage in P1 rather than cutting it (it's ~10 minutes and saves a demo disaster if you refresh).

Push back on any of that, or if it looks right, I'll hand over a clean `SPEC.md` plus a starter `CLAUDE.md` ready to drop into the repo.
