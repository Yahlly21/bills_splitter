# Conversation

---

## User

I want to consult with you regarding deploying an app on a free tier server.
CC asked me this:

Where will you deploy on the free tier?
❯ 1. Render (Recommended)
     Simplest FastAPI-from-GitHub deploy, free tier, single web service. Idle spin-down actually reinforces 'one-time use'.
  2. Railway
     Also easy, good FastAPI support, generous-ish free usage.
  3. Decide later
     Build deploy-agnostic (FastAPI app + requirements.txt + start command + Dockerfile) and choose at the end.

explain me the tradeoffs and the pros and cons of these options

---

## Assistant

Good instinct to dig into this before committing — and there's one outdated assumption in CC's framing worth flagging up front: Railway's "generous-ish free usage" is no longer really true in 2026, which changes the comparison meaningfully.

Here's how the three options actually stack up.

**Render (CC's recommendation)**

Render is the only one of these with a genuinely persistent free tier. It grants 750 free instance hours to each workspace per calendar month, which is enough to keep one service running essentially full-time. No credit card is required to sign up and deploy. FastAPI deploys cleanly from GitHub with auto-detected builds, no Dockerfile needed.

The catch is the spin-down: free web services spin down after 15 minutes of inactivity and restart on the next request, with spin-up taking about one minute (some sources report 30–60 seconds). CC's note that this "reinforces one-time use" is a fair read — if your app is genuinely meant to be used occasionally, the cold start is a non-issue and you stay comfortably inside the free hours. If you needed snappy always-on responses, it'd be annoying.

Two other constraints worth knowing: the instance is small (512 MB RAM, 0.1 CPU), and free web services have an ephemeral filesystem — any changes (uploaded files, local SQLite databases) are lost every time the service redeploys, restarts, or spins down, and you can't attach a persistent disk on the free tier. If you need to store state, you'd use their free Postgres, but note free Postgres databases expire after 30 days.

**Railway**

This is where CC's framing is stale. Railway killed its old generous free tier. It now provides a 30-day trial with $5 in usage credits, after which the free plan continues at $1/month with limited resources (up to 1 vCPU and 0.5 GB RAM per service). A credit card is required even for the trial. The practical problem: one minimal always-on service with 0.5 GB RAM costs roughly $0.80 to $1.00 per month, so you can keep one tiny app alive, but there is no room for a database alongside it, and most developers hit the ceiling faster than they expect, and when they do, their app stops without warning.

The developer experience is excellent and arguably the smoothest of the bunch, and billing-by-the-second can be cheaper for bursty workloads. But there have also been recurring outages in 2025–2026, including a May 2026 platform-wide outage that took the API and databases offline for roughly 8 hours. For a free hobby deploy, Railway effectively means "free for ~30 days, then a trickle." It's not a stable zero-cost home.

**Decide later / deploy-agnostic**

The cost here is mostly your time and a slightly more complex setup up front: a Dockerfile, clean `requirements.txt`, and a parameterized start command (reading `$PORT` from the environment rather than hardcoding). The upside is real optionality — both Render and Railway accept a Dockerfile, and so do Fly.io, Koyeb, and others, so you're never locked in. The honest counterpoint is that FastAPI is *already* close to deploy-agnostic; the portability work is small, and Render-style git-push deploys don't even need the Dockerfile. So "decide later" mostly buys you insurance you may not cash in.

**My read for your situation**

If this is the one-time-use / low-traffic app CC seems to think it is, Render is the sensible default: no card, a real free tier you won't age out of in 30 days, and spin-down that costs you nothing when idle. The deploy-agnostic path is worth doing *lightly* regardless — write a `Dockerfile` and read `$PORT` from the environment so you're portable — but then just deploy to Render now rather than deferring the decision. Railway I'd only reach for if you specifically want its UX and are okay paying a few dollars a month once the trial lapses.

One thing that would sharpen this: does your app need to persist any data between uses (a database, uploaded files), or is it stateless? That's the detail that most affects whether Render's free tier fits cleanly or needs a workaround.

---

## User

This is the app I will deploy
Every Friday you meet a few of your friends at a coffee shop for brunch. When the meal is done and everyone's ready to go home, there's often an awkward dance around the bill. Who ordered what? How do we split the tip?
Build a web app that solves this problem. Make sure to spend less than two hours

what is your take now?

---

## Assistant

Now that I know the app, my take gets simpler and more confident: Render, and don't overthink the rest.

Here's why this app is almost a textbook fit for Render's free tier. It's used once a week by a handful of people, so traffic is near-zero and bursty. The spin-down that I flagged as the main downside last time basically dissolves here — a 30–60 second cold start when the first person opens the app on Friday morning is completely fine for a casual brunch tool, and once everyone's actively using it the instance stays awake. You'll use a tiny fraction of the 750 monthly hours. No credit card, git-push deploy, done.

The other wrinkles I raised also mostly evaporate once you look at what this app needs to store, which is: almost nothing. The crux is a design decision you're implicitly making:

The simplest two-hour version is fully stateless. One person at the table enters the items and prices, taps to assign each item to whoever ordered it, enters a tip percentage, and the app computes per-person totals. Nothing is saved; a refresh starts over, and that's fine because the bill only matters for the next five minutes. With this version, Render's ephemeral filesystem and the 30-day Postgres expiry are completely irrelevant — there's no database at all.

The nicer version is a shared room: one person creates a session, friends open a link on their phones and each claims their own items. That needs shared state across requests, but it can live in an in-memory dict keyed by a room ID — no database required. It survives as long as the instance is awake, which easily covers one brunch. You'd only risk losing it if the table went 15 minutes with zero interaction mid-meal, which is unlikely and low-stakes anyway. So even here you don't need durable storage, and Render's free-tier limitations still don't bite.

Given the under-two-hours budget, I'd also walk back the "write a Dockerfile" suggestion from before. The fastest path is just a FastAPI app plus `requirements.txt` pushed to GitHub, with Render auto-detecting the build — no Dockerfile needed. That portability insurance isn't worth 15 minutes of a 120-minute budget for an app this small. Read `$PORT` from the environment (that's a one-liner and the only deploy-specific thing you need), and ship.

So: pick the stateless or in-memory version depending on whether you want the shared-phone experience, skip the database entirely, and deploy straight to Render. Want me to sketch the FastAPI structure for whichever version you're leaning toward?

---

## User

save this conversation as an md file (all of it - no summary - raw)
