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

Initial assumption: GitHub gives you 5,000 requests/hour with a token. Reality: that's for the core API only. **Code search is 30 requests/minute.** That's a 10x difference from what I expected.

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

## Phase 1: Core Search — [dates TBD]

*Entries go here as you build. Template:*

### YYYY-MM-DD — Title

What happened. Why it matters. The specific details.

**Content angle:** One-line hook for a potential LinkedIn post or article.

---

## Phase 2: Contact Enrichment — [dates TBD]

---

## Phase 3: Resume + AI Outreach — [dates TBD]

---

## Phase 4: Polish + Scale — [dates TBD]

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
