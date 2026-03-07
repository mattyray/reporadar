# RepoRadar — Skills Demonstrated

> This document tracks the specific technical skills demonstrated in building RepoRadar.
> Used for resume updates, portfolio descriptions, interview talking points, and LinkedIn content.
> Update as each feature is built.

---

## Architecture & System Design

| Skill | Where Demonstrated | Notes |
|-------|--------------------|-------|
| Multi-provider adapter pattern | `providers/base.py`, `hunter.py`, `apollo.py` | Abstract base class with swappable implementations |
| OAuth 2.0 flow (Google + GitHub) | `accounts/` app + django-allauth | Separate identity from data access pattern |
| Background job orchestration | Celery tasks for scan/enrich/parse | Multi-step workflows with status tracking |
| API rate limit management | `providers/github_client.py` | Per-user rate limits via OAuth tokens, Redis caching to minimize API hits |
| Multi-layer caching strategy | Redis (hot) + PostgreSQL (warm) | Different TTLs per data type, cache-first on all external API calls |
| Credit-aware API integration | Hunter.io free endpoint pre-check | Call Email Count (free) before Domain Search (costs credits) |
| BYOK credential management | `accounts/models.py` APICredential | Fernet encryption at rest, per-user isolation |

## Backend Engineering

| Skill | Where Demonstrated | Notes |
|-------|--------------------|-------|
| Django 5 + DRF | Full backend API | JWT auth, serializers, viewsets |
| PostgreSQL | Data model, caching layer | Structured prospect data, enrichment results |
| Redis | API response caching, Celery broker | TTL-based invalidation |
| Celery | Async task processing | GitHub scanning, enrichment, AI generation |
| TDD with pytest | `tests/` directory | Tests written first, business logic in pure functions |
| django-allauth | Multi-provider OAuth | Google (identity) + GitHub (data access) |

## Frontend Engineering

| Skill | Where Demonstrated | Notes |
|-------|--------------------|-------|
| React 19 + TypeScript | Full frontend app | |
| Vite | Build tooling | |
| Tailwind CSS | Styling | |
| TanStack Query | Data fetching, cache management | Polling for async job status |

## AI/ML Integration

| Skill | Where Demonstrated | Notes |
|-------|--------------------|-------|
| Claude API | Resume parsing, outreach generation | Structured extraction from unstructured documents |
| Prompt engineering | Resume parser + outreach generator | Two-sided personalization (user profile + company data) |
| AI-generated content with human context | Outreach messages | References specific repos, stack overlap, shared tools |

## External API Integration

| Skill | Where Demonstrated | Notes |
|-------|--------------------|-------|
| GitHub REST API v3 | Code search, repo analysis, org/contributor data | OAuth token management, rate limit handling |
| Hunter.io API v2 | Domain search, email finding, verification | Credit tracking, free endpoint optimization |
| Apollo.io API | Contact enrichment (optional) | Adapter built, requires paid plan |

## DevOps & Infrastructure

| Skill | Where Demonstrated | Notes |
|-------|--------------------|-------|
| Docker | Local dev environment | docker-compose for Redis + Postgres |
| Railway | Backend deployment | |
| Netlify | Frontend deployment | |
| CI/CD | GitHub Actions | Test suite runs on every PR |

## Product & Business

| Skill | Where Demonstrated | Notes |
|-------|--------------------|-------|
| Freemium SaaS design | Tier structure | Free (GitHub data) → Paid (enrichment + AI) |
| Developer tool UX | Search config, prospect cards, enrichment flow | |
| Data privacy | Encryption at rest, user data deletion, clear retention policy | |

---

## How to Use This Document

**For resume/portfolio:** Pull specific skills and "where demonstrated" into project descriptions.

**For interviews:** Each row is a potential talking point. The "notes" column gives the specific technical detail.

**For LinkedIn content:** Each skill area is a potential post topic. Combine with BUILD_LOG.md entries for war stories with technical depth.
