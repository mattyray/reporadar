# RepoRadar — Build Log

> Every architecture decision, bug fix, pivot, and lesson learned.
> This is raw material for LinkedIn posts, Substack articles, and interview stories.
> Write entries as you build — the details are freshest in the moment.

---

## How to Write Entries

Each entry should capture:
- **What happened** — the decision, bug, or discovery
- **Why it matters** — the tradeoff, the consequence, the insight
- **The specific details** — numbers, error messages, code patterns. This is what makes content real.

Format: date, title, body. Keep it conversational — this is your voice, not a corporate changelog.

---

## Pre-Build Research — March 2026

### 2026-03-07 — The Problem That Sparked the Project

Started from a personal pain point: job searching on LinkedIn is broken. Posts are old, ghost jobs everywhere, applications go into a black hole. The insight: if I want to find companies that build the way I build (Django, LangGraph, Claude Code), the signal isn't on LinkedIn — it's on GitHub.

Companies that use Claude Code put a `CLAUDE.md` file in their repos. Companies using specific stacks have `requirements.txt` and `package.json` files I can read. The hiring manager's GitHub profile often has their email, company, and bio. All public data, just nobody's connected the dots into a tool.

**Content angle:** "I stopped applying to LinkedIn jobs and started reading dependency files instead"

### 2026-03-07 — GitHub API Rate Limits Almost Killed the Architecture

Initial assumption: GitHub gives you 5,000 requests/hour with a token. Reality: that's for the core API only. **Code search is 10 requests/minute.** That's a 10x difference from what I expected.

This forced a major architecture decision: every user needs their own OAuth token so they get their own rate limits. If we used a single server token, the entire app would share 30 searches/minute across all users. Dead on arrival.

Solution: GitHub OAuth as a connected service. User clicks "Connect GitHub," we get their token, and their searches use their own rate limit pool. Caching in Redis (24hr TTL on search results) means repeat queries don't burn rate limit at all.

**Content angle:** "The API rate limit that changed my entire architecture"

### 2026-03-07 — Why Google OAuth for Identity, GitHub OAuth for Data

First instinct: "Sign in with GitHub" for everything. Then realized: recruiters and hiring managers might want to use this tool too, and they might not have GitHub accounts.

Separated identity (who you are = Google, everyone has one) from data access (what you can do = GitHub, Hunter, Apollo as connected services). Same pattern as Vercel, Railway, Netlify.

django-allauth handles both OAuth providers and auto-links accounts when emails match.

**Content angle:** "Separating identity from capability — an auth pattern more apps should use"

### 2026-03-07 — Hunter.io vs Apollo.io — The Objective Comparison

Needed contact enrichment for the second layer of the app. Did a deep dive on both.

Hunter.io: smaller database but clean API available on ALL plans including free (25 searches/month). Has a free Email Count endpoint — can check if data exists before spending a credit. Well-documented, reliable, purpose-built for email finding.

Apollo.io: massive database (210M+ contacts), generous free email credits (10K/month with corporate domain). BUT: advanced API access locked behind $119/month Organization plan. Free tier is designed to get you clicking around their UI, not building on their data programmatically.

Decision: Hunter.io as default enrichment provider (API accessible on free tier), Apollo as optional adapter for users who already have paid accounts. Built the enrichment layer as provider-agnostic with swappable adapters so adding new providers is trivial.

**Content angle:** "I evaluated 8 contact data APIs — here's what actually matters for developers"

### 2026-03-07 — The Freemium Model That Makes Sense

Studied how Simplify works: most features free, premium for power users. Applied the same logic:

Free tier costs me almost nothing to run — it's all GitHub's API using the user's own token. The expensive parts (Hunter API calls, Claude API for resume parsing and outreach) are the paid features, and even those start as BYOK (user brings their own key) so my cost is zero.

The caching layer is actually the hidden monetization engine: once ANY user scans a company, that data is cached for 30 days. The second user who finds the same company gets instant results. The database of "companies building with X stack" grows organically and becomes the real asset.

**Content angle:** "Building a SaaS with zero infrastructure costs — the BYOK model"

---

## Phase 1: Core Search — March 2026

### 2026-03-07 — django-cryptography Doesn't Support Django 5

Planned to use django-cryptography to encrypt user API keys (Hunter, Apollo) at rest. Deep research caught that it hasn't been updated for Django 5 — would've been a runtime crash during the first migration.

Switched to django-fernet-encrypted-fields (Jazzband fork). Same Fernet encryption, actively maintained, drop-in replacement. Import path is `from encrypted_fields import EncryptedCharField` — not obvious from the package name.

**Content angle:** "The dependency that would've broken my app on day one — and how pre-build research saved me"

### 2026-03-07 — allauth's Hidden Superpower: Built-in Headless JWT

Original plan: django-allauth for OAuth + dj-rest-auth + simplejwt for JWT tokens. Three packages for auth. During research, discovered allauth v65+ has a built-in headless mode with its own JWT strategy (`JWTTokenStrategy`). Eliminated two dependencies.

But getting the import paths right was a war. Tried 4 different paths before finding the real one buried in the package: `allauth.headless.tokens.strategies.jwt.strategy.JWTTokenStrategy`. Had to literally inspect the installed package's file tree inside the Docker container. The docs don't mention the full path.

Also hit deprecated settings: `ACCOUNT_AUTHENTICATION_METHOD` and `ACCOUNT_EMAIL_REQUIRED` are gone in modern allauth. Replaced with `ACCOUNT_LOGIN_METHODS = {"email"}` and `ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]`.

**Content angle:** "I deleted 2 auth packages by reading the source code of the third"

### 2026-03-07 — 54 Tests Before a Single View Worked

Wrote tests first for all the pure business logic: stack detection (parsing requirements.txt, package.json, pyproject.toml), scoring algorithm (0-100 based on stack match, AI signals, production signals, activity, team size), GitHub client, and Hunter provider. 54 tests, all passing, before the first API endpoint returned a response.

The stack detection tests use real fixture files — actual requirements.txt and package.json from known projects. The scoring tests cover edge cases: perfect match (100), zero match (0), mixed signals. Provider tests mock HTTP responses so they run fast and don't hit real APIs.

**Content angle:** "54 tests before my first endpoint — what TDD actually looks like in practice"

### 2026-03-07 — Full-Stack Frontend in One Shot

Scaffolded the entire React frontend: 8 pages (Login, Search, Prospects, Prospect Detail, Settings, Outreach, Auth Callback), a Layout with nav, an auth hook, a typed API client covering all 20+ endpoints, and TypeScript interfaces matching every backend serializer. TanStack Query handles data fetching with automatic polling for search status (3-second interval while running). Protected routes redirect to login. Clean TypeScript compile on first try.

**Content angle:** "How I scaffolded a production React frontend in under an hour with AI pair programming"

### 2026-03-07 — "Click Click Click Work" — The UX Redesign

Rebuilt the frontend around a philosophy: users shouldn't have to figure anything out. Added a setup checklist (connect GitHub, upload resume, add API keys), tech chip selector that auto-populates from your resume, and action cards on company detail pages. Every action is one click — save, enrich, outreach. No forms, no configuration, no reading docs.

The resume auto-detect is the best example: upload a PDF, Claude parses it, your tech stack auto-fills in the search bar, hit search. Three clicks from "I just signed up" to "here are companies hiring for my stack."

**Content angle:** "The UX principle that made my side project actually usable"

### 2026-03-07 — The Competitive Landscape Panic (That Wasn't)

Had a moment of "does this already exist?" Deep research found: BuiltWith/Wappalyzer detect tech from websites (frontend only, miss backend entirely). StackShare is self-reported and outdated. HG Insights/Slintel are $$$$ enterprise. Clay could theoretically replicate the workflow but costs $149+/month and requires manual setup.

Nobody is doing GitHub-native tech detection + ATS job board cross-referencing + resume-matched outreach. The AI tool signal detection (CLAUDE.md, .cursor, copilot) is completely novel. Competitive moat is the approach, not the tech.

**Content angle:** "I thought my app already existed — here's what I found when I actually looked"

---

## Phase 2: ATS Job Board Integration — March 2026

### 2026-03-07 — Four Free APIs Nobody Talks About

Discovered that Greenhouse, Lever, Ashby, and Workable all have completely free, public, no-auth-required APIs for their job boards. These are designed for companies to build custom career pages, but nothing stops you from aggregating them.

The catch: none support keyword search. You need to know the company slug first, then fetch ALL their jobs, then filter client-side. For RepoRadar this is perfect — we already know the company from GitHub. Try their org name as the ATS slug, and if it works, we have their entire job board.

Built an ATSClient provider that probes all four platforms in parallel using ThreadPoolExecutor. A single call tests a company across all four ATS platforms in ~2 seconds. The probe runs automatically whenever GitHub search discovers a new org, so the job database grows organically.

Tech extraction from job descriptions reuses the same ~80 tech keyword list from the GitHub detection module. A "Senior Django Engineer" posting that mentions "React, PostgreSQL, and Docker" gets tagged with all four techs. Users can then search the Jobs page for "Django" and find roles they'd never have found through traditional job boards.

**Content angle:** "The free APIs that power a job board nobody's built yet"

### 2026-03-07 — The Slug Problem

The hardest part of ATS integration isn't the API — it's figuring out the slug. Stripe's Greenhouse board is at `boards.greenhouse.io/stripe`. Easy. But some companies use different slugs than their GitHub org name. Scale AI is `scaleai` on Greenhouse, not `scale-ai`. Neon Database is `neondatabase`.

Current approach: try the GitHub login as-is, plus the company name with spaces removed, plus the name with hyphens. It's a heuristic, not perfect. Seeded 55+ known tech company mappings as a starting point. Every successful probe gets cached permanently — the mapping database improves over time.

Future idea: scrape company websites for career page links (they often contain the ATS slug in the URL). But for now, the brute-force probe works surprisingly well.

**Content angle:** "The unglamorous data problem behind every aggregation startup"

### 2026-03-07 — 132 Tests, Zero Regressions

Added the entire jobs feature — new Django app, ATS provider, Celery tasks, 3 API endpoints, frontend Jobs page, company detail integration, hiring badges — and the existing 89 tests didn't break. 43 new tests for tech extraction (pure function, 14 tests), ATS client (mocked HTTP for all 4 platforms, 13 tests), and API endpoints (16 tests). TDD made this possible: business logic in pure functions, providers behind adapters, views are thin.

**Content angle:** "How TDD let me add a major feature without touching a single existing test"

---

## Phase 3: Contact Enrichment — [dates TBD]

---

## Phase 4: Resume + AI Outreach — [dates TBD]

---

## Phase 5: Polish + Scale — [dates TBD]

---

## Content Pipeline

### Published
| Date | Platform | Title | Link |
|------|----------|-------|------|
| | | | |

### Drafted (from build log entries above)
| Entry Date | Working Title | Status |
|------------|---------------|--------|
| | | |

### Ideas (not yet written)
| Hook | Source Entry | Priority |
|------|-------------|----------|
| "I stopped applying to LinkedIn jobs and started reading dependency files" | 2026-03-07 problem statement | High — origin story |
| "The API rate limit that changed my entire architecture" | 2026-03-07 rate limits | High — technical war story |
| "Building a SaaS with zero infrastructure costs" | 2026-03-07 freemium model | Medium — business/technical crossover |
| "Separating identity from capability in auth design" | 2026-03-07 auth pattern | Medium — architecture deep dive |
| "The free APIs that power a job board nobody's built yet" | 2026-03-07 ATS integration | High — unique angle, practical |
| "I thought my app already existed" | 2026-03-07 competitive landscape | Medium — founder story |
| "How TDD let me add a major feature without touching a single existing test" | 2026-03-07 132 tests | Medium — engineering credibility |
