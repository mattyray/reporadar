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

## Deployment — March 2026

### 2026-03-08 — Railway Deployment: Four Bugs Stacked on Top of Each Other

Deploying the Django backend to Railway took ~12 iterations. Not because any single problem was hard, but because four separate issues were stacked on top of each other, each one masking the next. Here's every problem in the order I hit them, and how each was fixed.

**Bug 1: "host 'db' not found"**

The app crashed immediately on Railway because `DATABASE_URL` defaulted to `postgresql://reporadar:reporadar@db:5432/reporadar` — that's the Docker Compose hostname from local dev. Railway doesn't have a container called `db`. Fix: set `DATABASE_URL` as a Railway env var pointing to the actual Postgres instance (`turntable.proxy.rlwy.net:22079`). Also had to set the root directory to `/backend` so Railway knew where the Dockerfile was.

**Bug 2: Docker cache serving stale code**

Pushed code fixes but the deploy logs showed every Docker layer as `CACHED` — Railway was reusing the old image. The `COPY . .` layer was cached because Docker didn't detect changes (layer cache is content-addressed, but Railway's builder was aggressively caching). Fix: added a `# Cache bust: 2026-03-08` comment to the Dockerfile to invalidate the layer cache. Hacky, but it worked immediately.

**Bug 3: Healthcheck failing — three sub-problems**

Railway's healthcheck kept marking the service as unhealthy even though gunicorn was starting fine. Three things were wrong simultaneously:

1. `SECURE_SSL_REDIRECT = True` in production.py — Railway's internal healthcheck sends HTTP requests, and Django was redirecting them to HTTPS, which the healthcheck interpreted as failure. Fix: removed `SECURE_SSL_REDIRECT` entirely. Railway handles SSL termination at the proxy layer, so Django should never redirect to HTTPS itself.

2. Internal Railway networking (`postgres.railway.internal`) DNS wasn't resolving — the app couldn't finish startup because it was hanging on database connections. Fix: switched to public database/Redis URLs. Internal networking requires specific Railway networking configuration that wasn't set up.

3. Port mismatch — Railway auto-assigns a port via the `PORT` env var (was 8080), but the public domain was configured for a different port. Fix: made gunicorn bind to `[::]:${PORT:-8000}` to respect whatever port Railway assigns. The `[::]` syntax binds both IPv4 and IPv6.

After fighting all three, I removed the healthcheck from `railway.json` entirely to unblock the deploy. The service started fine — it was just the healthcheck that couldn't reach it.

**Bug 4: 400 Bad Request on every endpoint**

Service was running, port was right, but hitting `/api/health/` returned 400. This is Django's `ALLOWED_HOSTS` validation — if the incoming `Host` header doesn't match an entry in `ALLOWED_HOSTS`, Django returns 400 (not 403, not 500 — 400). Setting `ALLOWED_HOSTS=*` should have worked but didn't reliably. Fix: set `ALLOWED_HOSTS=reporadar-production.up.railway.app` with the explicit domain. This is also better security practice — the `*` wildcard disables Host header validation entirely.

**What I Learned**

The real lesson: when debugging a deployment that isn't working, you might be looking at problem #3 while problems #1 and #2 are still unfixed underneath. Each fix revealed the next bug. The order matters — you can't debug a 400 response if the service isn't even starting, and you can't debug startup if Docker is serving cached code from three commits ago.

Also learned: Railway-specific gotchas aren't well-documented. The SSL redirect + healthcheck interaction, the internal networking DNS requirements, and the port assignment behavior were all trial-and-error discoveries.

**Production deployment config that works:**
- `railway.json`: DOCKERFILE builder, `bash start.sh` as start command, no healthcheck (for now)
- `start.sh`: runs migrations, then `exec gunicorn config.wsgi:application --bind [::]:${PORT:-8000}`
- `production.py`: no `SECURE_SSL_REDIRECT`, has `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, WhiteNoise for static files
- Env vars: explicit `ALLOWED_HOSTS` (not `*`), public database/Redis URLs, `DJANGO_SETTINGS_MODULE=config.settings.production`

**Content angle:** "Four bugs stacked on top of each other — what deploying Django to Railway actually looks like"

---

### 2026-03-08 — Netlify Frontend + Google OAuth: The Proxy Trap

Deployed the React frontend to Netlify (`reporadar-app.netlify.app`). The `netlify.toml` proxies `/api/*` and `/_allauth/*` to the Railway backend using `status = 200` redirects. This works great for normal API calls, but completely breaks OAuth.

**The trap:** Netlify's `status = 200` proxy follows HTTP redirects server-side. When allauth returns a 302 redirect to Google's OAuth page, Netlify follows that redirect itself and returns the Google HTML to the browser as if it were a 200 response from the original URL. The browser never sees the 302, never navigates to Google, and the OAuth flow is dead.

**Fix:** Skip the Netlify proxy entirely for OAuth. The "Sign in with Google" button sends the browser directly to `https://reporadar-production.up.railway.app/api/auth/google/start/`. This means the browser navigates to Railway, gets the 302 to Google, and the OAuth flow works as designed.

Also discovered that `HEADLESS_ONLY = True` in django-allauth blocks ALL browser-based views, including `OAuth2LoginView`. This is correct for a headless SPA, but it means you can't use allauth's standard OAuth flow at all. Had to remove it and include `allauth.urls` for the callback handler.

**Current status:** Flow reaches Google account chooser. User can select their account. But the callback to Railway returns "Third-Party Login Failure" — debugging the token exchange next.

**Content angle:** "The proxy trap — why your OAuth flow breaks on Netlify (and how to fix it)"

---

### 2026-03-09 — The JWT Signing Key Nobody Told Me About

Google OAuth was working — user could pick their Google account, allauth would process the callback, create/authenticate the user — but then the response was a 500 error. Every. Single. Time.

The Railway logs showed the traceback: `ValueError: Could not deserialize key data` inside allauth's JWT token creation. The problem: allauth's `JWTTokenStrategy` defaults to **RS256** (asymmetric signing), which requires an RSA private key configured via `HEADLESS_JWT_PRIVATE_KEY`. We never set one. So allauth tried to parse an empty string as a PEM-encoded RSA key and exploded.

The fix was one line: `HEADLESS_JWT_ALGORITHM = "HS256"`. Symmetric signing uses Django's `SECRET_KEY` automatically — no extra env vars, no key generation, no key rotation to worry about. For a single-server app with no token sharing between services, HS256 is perfectly fine.

**The real lesson:** The OAuth flow had been working for commits — the "Third-Party Login Failure" from the previous session was actually a different bug (credential mismatch) that was already fixed. The 500 was a NEW bug introduced when we added the custom `oauth_callback` view that generates a JWT to pass to the frontend. The token exchange with Google was succeeding, but we crashed trying to package the result. Classic "last mile" failure.

Also killed allauth's ugly unstyled "Sign In Via Google — Continue" confirmation page. allauth's `OAuth2LoginView` shows a confirmation form on GET but redirects to Google on POST. One line fix: `request.method = "POST"` before calling the view. Users now go straight from "Sign in with Google" to the Google account chooser — no intermediate page.

**Content angle:** "The default that broke my OAuth — why allauth's JWT needs a one-line config change"

---

### 2026-03-09 — GitHub OAuth: The Cross-Domain Session Problem

After Google OAuth was working, next step was GitHub — but GitHub isn't a login provider, it's a "connected service." User logs in with Google, then clicks "Connect GitHub" to link their GitHub account for API access. Allauth calls this the `process=connect` flow.

The problem: frontend is on Netlify (`reporadar-app.netlify.app`), backend is on Railway (`reporadar-production.up.railway.app`). Different domains = no shared cookies. When the user clicks "Connect GitHub," their browser goes to Railway, but Railway has no idea who they are — no session cookie, no authentication.

**Attempt 1: Just send them to the endpoint.**
Failed. Railway sees an anonymous user and allauth treats it as a signup/login, not a "connect." Even if the OAuth succeeds, the GitHub account gets created as a new user instead of being linked to the existing Google-authenticated account.

**Attempt 2: Pass the JWT token in the URL.**
The frontend stores a JWT (from Google login) in localStorage. We pass it as `?token=<jwt>` when navigating to Railway. The `github_start` view validates the JWT using allauth's `validate_access_token()` from `allauth.headless.tokens.strategies.jwt.internal`, then calls `django.contrib.auth.login()` to establish a Django session. Now Railway knows who the user is.

This worked — the logs showed "authenticated user mnraynor90@gmail.com via JWT" — but GitHub still wasn't linking to the account.

**Attempt 3: The missing `process=connect` parameter.**
Allauth's OAuth views check for a `process` parameter to decide behavior. Default is `AuthProcess.LOGIN` (create/login a user). For linking, you need `AuthProcess.CONNECT`. The fix:

```python
request.POST = QueryDict(mutable=True)
request.POST["process"] = "connect"
```

This tells allauth "this user is already logged in, link this GitHub account to their existing account." Without it, allauth either creates a duplicate user or fails with an email conflict.

**Also hit: JWT expiration.**
Allauth's default JWT lifetime is 300 seconds (5 minutes). Users who logged in more than 5 minutes ago got "invalid token" errors when trying to connect GitHub. Bumped to 86400 seconds (24 hours) with `HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 86400`.

**The full flow that works:**
1. User logs in with Google → gets JWT → stored in localStorage
2. User clicks "Connect GitHub" → browser goes to `railway.app/api/auth/github/start/?token=<jwt>`
3. Backend validates JWT → logs user into Django session → sets `process=connect` → redirects to GitHub
4. User authorizes on GitHub → callback hits Railway → allauth links GitHub to existing account
5. Backend redirects to `netlify.app/settings?github=connected` → frontend refetches profile

**Content angle:** "The cross-domain OAuth problem nobody warns you about — and the 3-layer fix"

---

### 2026-03-11 — Detecting What AI Tools Companies Build With

Added detection for 15 AI coding tools by checking for config files in repos: Claude Code (CLAUDE.md), Cursor (.cursorrules), Copilot, Windsurf, Aider, Codeium, Continue.dev, Bolt.new, v0, Lovable, Google IDX, Amazon Q, Cline, Roo Code, and OpenAI Codex. Each is a single HEAD request against the GitHub API — cheap, definitive, and no false positives. If a repo has a `.cursorrules` file, someone on that team is using Cursor. Period.

Also added zero-cost detection from GitHub's own data: the `language` field (25 languages mapped) and `topics` array (90+ topic-to-tech mappings). Every repo already returns this data — we were just ignoring it. Now a Go repo with topics `["kubernetes", "docker", "openai"]` gets tagged with all four technologies without parsing a single dependency file.

The frontend groups detections by category with color-coded chips: indigo for tech stack, purple for AI tools, gray for infrastructure. Search results now show at a glance: `[Django] [React] | [Claude Code] [Cursor] | [Docker] [CI/CD]`. The pipe separators make it scannable — you can instantly tell if a company builds with AI tools.

Built an AI tool selector in the search form — 15 purple toggle chips. Users can search specifically for "companies using Claude Code + Cursor" without even specifying a tech stack. This queries GitHub's code search for the actual config files (`filename:CLAUDE.md`, `filename:.cursorrules`).

**Content angle:** "How I detect which AI tools companies use — by reading their config files"
**Content angle:** "The GitHub data you're already paying for but not using"

### 2026-03-12 — AI Repo Analysis: Reading Code So You Don't Have To

Built a feature that sends a repo's entire structure to Claude and gets back a deep analysis: what the project does, its full tech stack, architecture patterns, code quality signals, team maturity estimate, and a "why work here" section for job seekers. The whole thing runs as a Celery background task and takes 30-60 seconds per repo.

The approach: fetch the repo's file tree via GitHub's Trees API (single request, returns every file path), then selectively pull ~50 key files — README, dependency files, config files, entry points, CI/CD configs. Each file is capped at 8K chars, total context capped at 60K chars. Send all of it to Claude Sonnet with a structured JSON prompt. No repo cloning, no git operations, pure API calls.

The prompt engineering was the interesting part. Claude returns a structured JSON object with: `tech_stack` (languages, frameworks, databases, infrastructure, notable libraries, AI tools), `architecture` (pattern name, description, key directories with purposes), `code_quality` (tests, CI/CD, linting, type checking, documentation), `maturity` (stage, signals, team size estimate, activity assessment), and `interesting_for_job_seekers` (why work here, tech culture signals, potential roles). That last section is what makes this different from generic code analysis — it's opinionated about whether this is a place worth applying to.

Hit a UX problem immediately: users kept clicking the analyze button because there was no feedback that anything was happening. Added a spinner with "takes 30-60 seconds" text, plus stale task detection — if an analysis has been stuck for 5+ minutes, the button unlocks so you can retry. The 409 Conflict response for in-progress analyses prevents duplicate Celery tasks from piling up.

**Content angle:** "I built an AI that reads GitHub repos and tells you if you should work there"
**Content angle:** "The UX mistake that made users spam my API — and the one-line fix"

### 2026-03-12 — Company Search: "Just Let Me Type a Name"

The original flow only found companies through tech stack search — you'd search for "Django + React" and get a list of orgs. But what if you already know the company? A friend says "check out YCharts, they use Django" and you want to scan them directly. You'd have to search for their exact tech stack and hope they show up. Terrible UX.

Built a company search that lets you type a name and find their GitHub org instantly. Three-part architecture:

1. **Autocomplete** — As you type, hits GitHub's Users Search API (`/search/users?q=ycharts+type:org`) with 500ms debounce. Returns org name, avatar, and login. Dropdown appears below the input with clickable results.

2. **Scan** — Click a result, fires a Celery task that fetches the org's profile, grabs their top 20 repos (skipping forks), runs the full detection pipeline on each (dependency parsing, AI tool detection, infra signals), and probes all 4 ATS platforms for job listings. Reuses the exact same `_process_repo` function from tech stack search — zero code duplication.

3. **Status polling** — Frontend polls every 3 seconds. When done, redirects to the prospect detail page where you can see all their repos, tech stack, and jobs. Same page you'd see from a tech stack search result.

The `get_org_repos` method has a nice fallback: tries the `/orgs/{login}/repos` endpoint first, and if it 404s (because the account is a User, not an Organization), falls back to `/users/{login}/repos`. GitHub's search API returns both types, so this handles either transparently.

**Content angle:** "Two paths to the same data — why good products have multiple entry points"

### 2026-03-12 — ATS Slug Discovery: When Guessing Isn't Enough

The original ATS integration tried the GitHub org login as the ATS slug — `stripe` → `boards.greenhouse.io/stripe`. Works great for Stripe, terrible for most companies. Linear's GitHub org is `linear-app`, but their Ashby board is at `jobs.ashbyhq.com/linear`. No amount of string manipulation connects those.

Built a website scraper that solves this. When we know a company's website (from their GitHub org profile), we:
1. Fetch the homepage HTML
2. Regex for career/jobs page links (`/careers`, `/jobs`, `/work-with-us`, etc.)
3. Follow up to 5 of those links
4. Scan all the HTML for ATS embed URLs using platform-specific patterns

The patterns are dead simple — each ATS has a distinctive URL format:
- Greenhouse: `boards.greenhouse.io/{slug}` or `boards-api.greenhouse.io/v1/boards/{slug}`
- Lever: `jobs.lever.co/{slug}`
- Ashby: `jobs.ashbyhq.com/{slug}`
- Workable: `apply.workable.com/{slug}`

Tested on 5 companies: Vercel (found Greenhouse), Figma (found Greenhouse), Linear (found Ashby), Notion (found — platform varies), Datadog (found). 4 out of 5 discovered correctly. The one miss was a company with a careers page that loaded job listings via JavaScript (no server-rendered ATS URLs in the HTML).

Also seeded 41 known tech company ATS mappings as a baseline. Had to verify every single one — turns out half my original list was wrong. Notion, OpenAI, Linear, Ramp, Sentry, Render, Supabase, and Retool all moved from Greenhouse to Ashby. Companies switch ATS platforms more often than you'd think.

**Content angle:** "Companies don't stay on the same ATS — and why that broke my job board"
**Content angle:** "The 5-line regex that finds any company's job board"

### 2026-03-12 — Three Bugs That Made the Jobs Page Useless

Launched the Jobs page. Users searched for "React" and got zero results. Three bugs, all stacked:

**Bug 1: Case sensitivity.** Frontend sends `"react"` (lowercase), but the database stores `"React"` (canonical). PostgreSQL's `JSONField __contains` lookup is case-sensitive. A search for `"react"` literally could not find `"React"`. Fix: normalize all search terms through the `TECH_KEYWORDS` mapping (`"react"` → `"React"`) before querying.

**Bug 2: 20-result cap.** DRF's global `PAGE_SIZE = 20` was limiting ALL `ListAPIView` responses, including job search. With 3,700+ jobs in the database, users only saw 20. Fix: added a `JobSearchPagination` class with `page_size = 100` specifically for the jobs endpoint.

**Bug 3: No relevance sorting.** Results came back in arbitrary order. A job mentioning React, TypeScript, AND Node.js ranked the same as one mentioning only React. Fix: Django `Case/When` annotations that count how many of the user's selected techs appear in each job's `detected_techs`, then `ORDER BY -match_count, -posted_at`. Best matches first, then newest.

The frontend now shows "236 jobs found (showing first 100)" with the most relevant results on top. Three bugs, three fixes, completely different user experience.

**Content angle:** "Three bugs that made my feature look broken — and why case sensitivity is a silent killer"

### 2026-03-13 — First Real Users (Not Me)

Checked the production database and found 4 users — 2 of which aren't me. Andy (March 11) connected GitHub and searched for Python + JavaScript, got 22 results. Ajit (March 13) searched for 12 technologies at once — Python, Django, TypeScript, FastAPI, Next.js, Rust, AWS, Docker, Redis, Celery, PyTorch — and got 49 results with an average match score of 44.

Neither saved any prospects or uploaded resumes. Can't tell if they clicked into any company detail pages because we had zero analytics. Which led to...

**Content angle:** "My first two real users — what I learned from having zero analytics"

### 2026-03-14 — Privacy-Friendly Analytics: No Cookies, No Third Party

Built a complete analytics system in ~370 lines. Two models: `Session` (one per visitor per day, identified by SHA-256 hash of IP + User-Agent + date) and `PageView` (one per page hit, linked to session). Single endpoint: `POST /api/analytics/track/`.

The frontend `AnalyticsTracker` component uses React Router's `useLocation` hook to fire on every navigation. On page leave (or tab close), it sends time-on-page via `navigator.sendBeacon()` — the browser API designed for exactly this, fires even during `beforeunload`.

GeoIP via `ip-api.com` (free, no API key) — called once per session creation, not per page view. Bot detection checks User-Agent patterns, missing `Accept-Language` header, and datacenter city names (Ashburn, Boardman, etc.).

No cookies, no consent banners, no third-party scripts. Session identity is ephemeral (same person tomorrow gets a new hash because the date changes). GDPR-friendly by design. Auto-cleanup via Celery task deletes data older than 90 days.

**Content angle:** "I built analytics without cookies, consent banners, or third-party scripts"
**Content angle:** "The navigator.sendBeacon() API that makes time-on-page actually work"

---

## Phase 3: Multi-Source Job Aggregation — March 2026

### 2026-03-14 — From 52 ATS Slugs to 6,500+

The original ATS integration only had slugs for companies discovered through GitHub search — about 52 mappings. But GitHub search only finds companies with public repos. What about all the companies hiring for Django that don't have anything on GitHub?

Found an open-source repo (Feashliaa/job-board-aggregator) with 6,261 verified ATS slugs: 4,516 Greenhouse, 947 Lever, 798 Ashby. Built `seed_from_aggregator` management command that downloads all three JSON files and creates ATSMapping records. Runs on every deploy via `start.sh`.

The batch fetcher processes 50 mappings at a time with 2-second stagger between each, then recursively schedules the next batch. At ~25 companies/minute, it takes about 4 hours to churn through the full 6,500. But after the first run, daily refreshes only re-fetch mappings that haven't been checked in 24 hours.

Result: went from 4,018 ATS jobs to 7,000+ in the first batch, with thousands more coming as the fetcher works through the backlog.

**Content angle:** "How I 100x'd my job database with one open-source repo"

### 2026-03-14 — Four External Job Boards in One Afternoon

Added RemoteOK, Remotive, We Work Remotely, and HN Who's Hiring as job sources. Each has a different API/format:

- **RemoteOK**: JSON API at `/api`. Hit a 403 — they block non-browser User-Agents. Fixed with `Mozilla/5.0 (compatible; RepoRadar/1.0)` header.
- **Remotive**: Clean JSON API at `/api/remote-jobs?category=software-dev`. Returns 23 software jobs. Smallest source but high quality.
- **WWR**: RSS feeds (no JSON API). Used `feedparser` library. Company name is embedded in the title as "Company: Job Title" — parsed with string splitting.
- **HN Who's Hiring**: Hit the Algolia HN API for the monthly thread. Regex parser handles the pipe-delimited format (`Company | Role | Location | Salary`). 427 jobs from the latest thread.

Unified storage: all jobs go into the same `JobListing` table with a `source` field. Conditional unique constraints prevent duplicates: ATS jobs unique on `(ats_mapping, external_id)`, external jobs unique on `(source, external_id)`. Stale job cleanup marks jobs as inactive if they disappear from the next fetch.

Celery Beat schedules: RemoteOK/Remotive daily at 7am, WWR every 6 hours, HN on the 1st of each month, ATS refresh daily at 6am.

Frontend tabs let users filter by source. Attribution links required by RemoteOK and Remotive ("via RemoteOK" links back to their site).

**Content angle:** "Four job APIs, four different formats, one unified table"

### 2026-03-14 — Resume-to-Job Matching: "Upload Resume, See Matching Jobs"

Built the full flow: user uploads resume → Claude parses tech stack → system matches against all active jobs → dashboard shows "Jobs For You."

The matching algorithm is simple: for each job, count how many of the user's resume techs appear in the job's `detected_techs`. Score = overlap count. Top 200 matches stored in `ResumeJobMatch` table. Daily refresh via Celery Beat re-matches all users.

The tricky part was tech name normalization. Claude parses "Claude API" from the resume, but jobs detect "Claude". "OpenAI SDK" vs "OpenAI". "Django REST Framework" vs "Django". Fixed with a three-layer approach:
1. **Parse time**: normalize resume techs through `TECH_KEYWORDS` map with word-boundary regex matching
2. **Search time**: backend fuzzy-matches search terms against keyword map
3. **Display time**: frontend highlights chips using word-boundary comparison

The word-boundary part was critical — naive substring matching caused "django" to match "go" (because "go" is inside "djan**go**"). Switched to `\bgo\b` regex matching.

**Content angle:** "The substring matching bug that highlighted every technology on the page"

### 2026-03-14 — Sentry Integration: Two Projects, One Wrong DSN

Set up Sentry error monitoring for both backend (Django + Celery) and frontend (React). Django: `sentry-sdk[django,celery]` with `sentry_sdk.init()` in production.py. React: `@sentry/react` initialized in main.tsx. Both read DSN from env vars.

The smoke test caught a bug: hit `/sentry-debug/` (deliberate ZeroDivisionError), got a 500 on the page, but no error in Sentry. Turns out the DSN provided during Sentry project creation was for a *different* project than the one I was checking. The setup wizard showed one DSN, the project settings showed another. Classic setup mismatch — verified the correct DSN from Project Settings → Client Keys and updated Railway.

Frontend Sentry confirmed working via `throw new Error("smoke test")` in Chrome DevTools (using Chrome MCP automation).

Also discovered: Google OAuth blocks sign-in from Chrome instances running under automation ("Chrome is being controlled by automated test software"). Can't smoke test the full auth flow via MCP — have to test manually or hit API endpoints directly.

**Content angle:** "My error monitoring wasn't monitoring errors — the one-DSN mistake"

### 2026-03-14 — Outreach Improvements: Job Context + Async + Subject Lines

Three outreach upgrades shipped in the same session:

1. **Job context in prompts**: When generating an outreach message for a company, the Claude prompt now includes their open job listings. Instead of generic "I see you use Django," the message can say "I noticed you're hiring a Senior Backend Engineer — here's why I'd be a fit."

2. **Async generation**: Moved from synchronous API call to Celery task. Frontend shows "Generating..." state while the task runs. No more 30-second HTTP timeouts on long Claude responses.

3. **Email subject lines**: Claude now returns a `subject` field in addition to the message body. Frontend displays it separately. Outreach messages stored with subject for future reference.

**Content angle:** "Making AI outreach actually personal — why context beats templates"

## Phase 4: Jobs-First Pivot — March 2026

### 2026-03-15 — The Honest Pivot: GitHub Search Wasn't Finding Jobs

Had to face the truth: the GitHub repo scanning — the original core feature — hadn't actually helped find a single job. The company search, tech stack detection, AI tool signals, scoring algorithm — all technically impressive, none practically useful for landing interviews.

Meanwhile, the ATS job aggregation (built as a secondary feature) was sitting on **177,675 real job listings** from 5,046 companies across Greenhouse, Lever, Ashby, and Workable. The daily Celery beat refresh was silently building the most valuable part of the app. RemoteOK, Remotive, WWR, and HN Who's Hiring added another 600 listings.

The pivot: make job search the primary experience. Upload resume → see matching jobs → apply. GitHub company search becomes a secondary "Companies" tab for power users. The data was already there — the UX just wasn't pointing at it.

**What got cut:**
- Outreach (AI message generation via Claude) — removed entirely. Nobody was using it, and "generate a cold email" doesn't help as much as "here are 50 matching jobs."
- Enrichment (Hunter.io/Apollo.io contact finding) — removed entirely. Finding hiring manager emails is a solved problem with LinkedIn — we don't need to reinvent it.
- API keys section in Settings — no more Hunter/Apollo BYOK.
- The big amber "Connect GitHub to start" banner — GitHub is now optional, not required.

**What stayed:**
- The entire GitHub search pipeline — it just moved to the Companies tab
- ATS probing — keeps running, keeps feeding job data
- Resume parsing — became the primary onboarding flow
- All Celery beat schedules — untouched

**The numbers:** 167 insertions, 1,211 deletions across 18 files. More code removed than added. The best kind of refactor.

**Content angle:** "I deleted 1,200 lines of code and made my app 10x more useful"
**Content angle:** "The feature I built first was the feature nobody used — and the secondary feature was the product"

### 2026-03-15 — Tech Detection: 53% of Jobs Were Invisible

After pivoting to jobs-first, realized half the job database was useless. **94,811 out of 177,675 jobs (53%) had empty `detected_techs`** — meaning they'd never match anyone's resume search. The tech extraction was running, but the keyword list only had ~130 entries and was missing extremely common terms.

**The "Go" false positive disaster:** 19,597 jobs had `["Go"]` as their ONLY detected tech. Not Go the programming language — the English word "go" appearing in job descriptions like "you will go home knowing" and "as we go to market." A "Lead Dentist" job was tagged with Go. The keyword `"go"` matched on word boundaries, but "go" is just too common in English. Fix: removed `"go"`, kept `"golang"` as the only trigger for Go.

**Missing keywords (biggest impact):** SQL — the most common technology in engineering job descriptions — was completely absent from the keyword list. Also missing: C++, HTML, CSS, Linux, Git, React Native, Flutter, iOS, Android, Apache Spark, Snowflake, Airflow, dbt, Databricks, Spring Boot, ASP.NET, Blazor, Entity Framework, Webpack, Vite, and about 15 more. Added ~35 new keywords total.

**Reprocessing 185k jobs in production:** Wrote a `reprocess_all_job_techs` Celery task and a `reprocess_techs` management command. The Celery task worked locally but Railway's database kept killing the connection after ~60k rows. Switched to a raw SQL approach via `railway run` with fresh psycopg2 connections per batch of 200 rows and retry logic. Still hit connection drops but the retry logic kept it going.

**Results after reprocessing:** ~67k jobs updated. The Go false positive dropped from 14,291 → 0. New keywords lit up thousands of previously invisible jobs. Detection rate improved from 46.6% to roughly 65%+ with the new keywords catching SQL, Linux, HTML/CSS, Spring, and other common terms.

**The lesson:** Tech detection from job descriptions is fundamentally different from tech detection from dependency files. Dependency files are structured and unambiguous — `django==4.2` means Django. Job descriptions are free text where common English words collide with programming language names. Short keywords (Go, R, C) need special handling or they'll match everything.

**Content angle:** "53% of my job database was invisible — the keyword gap nobody checks"
**Content angle:** "The word 'go' ruined my tech detection for 20,000 jobs"

### 2026-03-15 — The Frontend Reorganization

The route swap was clean but had ripple effects everywhere:

**Navigation:** `Jobs | Companies | Settings` (was `Dashboard | Companies | Jobs | Outreach | Settings`). Three links instead of five. The Jobs tab renders what used to be the JobsPage, now enhanced with a welcome header, resume upload banner, and auto-triggered search when resume techs load.

**SetupChecklist redesign:** The old version had a massive amber banner screaming "CONNECT GITHUB OR ELSE." The new version leads with a calm blue "Upload your resume to get started" prompt. GitHub connection is demoted to a small "Also available" hint. This matches the new reality — you don't need GitHub to use the app.

**Auto-search on resume load:** When a user uploads their resume and tech chips auto-populate, the job search now fires immediately. No need to hit the "Search Jobs" button. Upload → results. Two interactions instead of three.

**ProspectDetailPage surgery:** Removed the "Find Email Contacts" and "Write Outreach Message" action cards. The 4-card grid became a 2-card grid (Save Company + Check Open Roles). Removed the entire Contacts section at the bottom. The page is cleaner and focused on what matters: repos, tech stack, contributors, and jobs.

**Landing page:** Updated the "How it works" steps — step 3 changed from "Generate personalized outreach" to "Apply directly." Simplified pricing from Free + Pro (BYOK) to just "Completely free." No more two-column pricing comparison. One card, one message: $0, no catch.

**Content angle:** "The UX surgery that turned a power tool into a product"

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
| "Four bugs stacked on top of each other — deploying Django to Railway" | 2026-03-08 Railway deployment | High — relatable war story |
| "I built an AI that reads GitHub repos and tells you if you should work there" | 2026-03-12 AI repo analysis | High — unique feature, AI angle |
| "The UX mistake that made users spam my API" | 2026-03-12 analyze button UX | Medium — relatable UX lesson |
| "Two paths to the same data — why good products need multiple entry points" | 2026-03-12 company search | Medium — product thinking |
| "Companies don't stay on the same ATS" | 2026-03-12 ATS slug discovery | Medium — data quality lesson |
| "The 5-line regex that finds any company's job board" | 2026-03-12 website scraping | High — practical, shareable |
| "Three bugs that made my feature look broken" | 2026-03-12 jobs page fixes | High — relatable debugging story |
| "My first two real users — what I learned from zero analytics" | 2026-03-13 first users | High — founder story |
| "I built analytics without cookies or consent banners" | 2026-03-14 analytics | High — privacy angle, practical |
| "I deleted 1,200 lines and made my app 10x more useful" | 2026-03-15 pivot | High — founder honesty, counterintuitive |
| "The feature I built first was the feature nobody used" | 2026-03-15 pivot | High — product lesson |
| "The word 'go' ruined my tech detection for 20,000 jobs" | 2026-03-15 tech detection | High — specific, memorable, shareable |
| "53% of my job database was invisible" | 2026-03-15 tech detection | Medium — data quality story |
| "The UX surgery that turned a power tool into a product" | 2026-03-15 frontend reorg | Medium — product design |
