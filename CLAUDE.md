# RepoRadar — GitHub-Powered Prospect Finder

## Overview
RepoRadar is a web application that helps engineers and job seekers find companies building with specific tech stacks by scanning GitHub organizations. It detects technologies from dependency files, identifies production signals, pulls contributor contact information, and enriches prospects with business emails via Hunter.io. Users can upload their resume for AI-generated personalized outreach messages.

**Target users:** Engineers looking for jobs at companies that match their stack, recruiters sourcing technical talent, and anyone who wants to find organizations building with specific technologies.

**Business model:** Free tier (GitHub search + stack detection + contributor info), paid tier (contact enrichment + AI outreach generation). Simplify-like model — most value is free, premium features for power users.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5, Django REST Framework |
| Auth | django-allauth (Google + GitHub OAuth), djangorestframework-simplejwt |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache | Redis (API response caching) |
| Task Queue | Celery + Redis (background scanning jobs) |
| AI | Claude API (resume parsing, outreach generation) |
| External APIs | GitHub REST API v3, Hunter.io API v2, Apollo.io API (optional) |
| Backend Hosting | Railway |
| Frontend Hosting | Netlify |

---

## Project Structure

```
reporadar/
├── CLAUDE.md                # Project context for Claude Code
├── SKILLS.md                # Technical skills demonstrated (for resume/LinkedIn)
├── BUILD_LOG.md             # Decisions, learnings, war stories (for content)
├── README.md
├── backend/
│   ├── apps/
│   │   ├── accounts/        # User profile, API key management, connected services
│   │   ├── search/          # GitHub search, stack detection, scoring
│   │   │   ├── detection.py # Pure functions: parse deps → detected techs
│   │   │   ├── scoring.py   # Pure functions: signals → score 0-100
│   │   │   ├── views.py     # Thin DRF views
│   │   │   ├── serializers.py
│   │   │   ├── tasks.py     # Celery tasks
│   │   │   └── models.py
│   │   ├── enrichment/      # Hunter.io, Apollo.io contact enrichment
│   │   ├── prospects/       # Prospect/org data, caching, saved lists
│   │   ├── resumes/         # Resume upload, parsing, profile storage
│   │   └── outreach/        # AI message generation
│   ├── providers/           # Provider-agnostic API adapters
│   │   ├── base.py          # Abstract base classes
│   │   ├── github_client.py # GitHub API adapter
│   │   ├── hunter.py        # Hunter.io adapter
│   │   └── apollo.py        # Apollo.io adapter
│   ├── tests/               # All tests live here (TDD)
│   │   ├── conftest.py
│   │   ├── fixtures/        # Sample dep files, API response mocks
│   │   └── test_*.py
│   ├── config/
│   │   └── settings/
│   │       ├── base.py
│   │       ├── development.py
│   │       └── production.py
│   ├── manage.py
│   ├── Dockerfile
│   └── Procfile
├── frontend/
│   ├── src/
│   │   ├── app/             # React Router pages
│   │   ├── components/      # Shared components
│   │   ├── hooks/           # TanStack Query hooks
│   │   ├── lib/             # API client, utils
│   │   └── types/           # TypeScript interfaces
│   ├── netlify.toml
│   └── vite.config.ts
└── docker-compose.yml
```

---

## Architecture Decisions

### Authentication — Google OAuth + Connected Services
- **Account creation:** Google OAuth via `django-allauth` — everyone has a Google account, zero friction signup
- **GitHub:** Connected service, NOT the login. User clicks "Connect GitHub" in settings, triggers GitHub OAuth flow (scopes: `read:org`, `public_repo`). We store the GitHub OAuth token encrypted alongside their account.
- **Hunter.io / Apollo.io:** Manual API key entry (BYOK). These services don't offer third-party OAuth. Keys encrypted with Fernet (django-cryptography).
- **Account linking:** django-allauth auto-links accounts when Google email matches GitHub email, preventing duplicates
- **Why this pattern:** Separates identity (Google = who you are) from data access (GitHub, Hunter, Apollo = connected services). Doesn't lock out non-GitHub users (recruiters, hiring managers). Same pattern as Vercel, Railway, Netlify.
- **Future:** Add email/password signup as fallback, Stripe billing for shared credentials

### GitHub API Strategy
- **GitHub access is via OAuth token** — obtained when user connects their GitHub account
- **OAuth scopes needed:** `read:org`, `public_repo` (read-only access to public repos and org data)
- **Code search requires authentication** — no anonymous searches for `filename:CLAUDE.md`
- **Search API rate limit: 30 requests/minute** (separate from the 5,000/hr core API limit)
- **Core API: 5,000 requests/hour** per authenticated user (repo details, contributors, file contents)
- Each user's GitHub OAuth token = their own rate limits
- Future: Register as a GitHub App for per-installation rate limits at scale
- **Caching is critical** — cache all GitHub responses in Redis (TTL: 24hrs for search, 7 days for repo/org data)

### Hunter.io API Strategy
- Free tier: 25 domain searches + 50 verifications/month
- **Email Count endpoint is FREE** — always call this first to check if Hunter has data before spending a credit
- Domain Search: 1 credit per 1-10 emails returned
- Rate limit: 15 req/sec, 500/min — very generous
- Test API key available for development: `test-api-key`
- Cache domain search results for 30 days in PostgreSQL

### Apollo.io API Strategy (Optional Provider)
- Free tier: 100 credits/month (10,000 email credits with corporate domain)
- **Advanced API access requires paid plan ($119+/month)** — document this clearly for users
- Build the adapter but label it as "requires Apollo paid plan"
- 210M+ contact database — much larger than Hunter when available

### Resume Parsing
- User uploads PDF or DOCX
- Claude API extracts: key projects, tech stack, years of experience, strongest talking points, personal story hook
- Stored as structured JSON in PostgreSQL
- Used by outreach message generator to personalize both directions (user → company)
- Privacy: encrypt at rest, user can delete anytime, clear data retention policy

### Caching Strategy
| Data | Cache Location | TTL |
|------|---------------|-----|
| GitHub code search results | Redis | 24 hours |
| GitHub repo details | PostgreSQL + Redis | 7 days |
| GitHub org details | PostgreSQL + Redis | 7 days |
| GitHub contributor profiles | PostgreSQL + Redis | 7 days |
| Stack detection results | PostgreSQL | 30 days |
| Hunter email count (free) | Redis | 24 hours |
| Hunter domain search | PostgreSQL | 30 days |
| Apollo contact data | PostgreSQL | 30 days |

### Background Jobs (Celery)
Scanning a GitHub org is slow (multiple API calls for repo contents, dependency files, contributors). Run as Celery tasks:
- `scan_search_results` — process code search results, filter orgs, queue repo analysis
- `analyze_repo` — detect stack, check infra signals, pull contributors
- `enrich_prospect` — hit Hunter/Apollo for contact data
- `parse_resume` — send to Claude API, store structured result
- `generate_outreach` — create personalized message via Claude API

Frontend polls for job status via DRF endpoint or uses SSE for real-time updates.

---

## API Endpoints

### Auth & Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/google/` | Initiate Google OAuth flow |
| GET | `/api/auth/google/callback/` | Google OAuth callback |
| GET | `/api/auth/github/connect/` | Initiate GitHub OAuth (connect service) |
| GET | `/api/auth/github/callback/` | GitHub OAuth callback |
| POST | `/api/auth/token/` | Get JWT from session (after OAuth) |
| POST | `/api/auth/token/refresh/` | Refresh JWT |
| POST | `/api/auth/logout/` | Logout |
| GET | `/api/accounts/me/` | Current user profile + connected services status |
| GET/PUT | `/api/accounts/api-keys/` | Manage Hunter/Apollo API keys |
| GET | `/api/accounts/api-keys/status/` | Check credit balances for each provider |
| DELETE | `/api/accounts/github/disconnect/` | Disconnect GitHub |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/search/` | Start a new search (returns job ID) |
| GET | `/api/search/{id}/status/` | Poll search job status |
| GET | `/api/search/{id}/results/` | Get search results |
| GET | `/api/search/history/` | Past searches |
| GET | `/api/search/presets/` | Saved search configurations |
| POST | `/api/search/presets/` | Save a search preset |

### Prospects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prospects/` | List all discovered prospects |
| GET | `/api/prospects/{id}/` | Prospect detail (org + repos + contacts) |
| POST | `/api/prospects/{id}/enrich/` | Trigger contact enrichment |
| POST | `/api/prospects/{id}/save/` | Save to user's prospect list |
| GET | `/api/prospects/saved/` | User's saved prospects |
| DELETE | `/api/prospects/saved/{id}/` | Remove from saved |
| GET | `/api/prospects/export/` | Export as CSV |

### Resumes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resumes/upload/` | Upload resume (PDF/DOCX) |
| GET | `/api/resumes/profile/` | Get parsed resume profile |
| PUT | `/api/resumes/profile/` | Edit parsed profile |
| DELETE | `/api/resumes/profile/` | Delete resume and parsed data |

### Outreach
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/outreach/generate/` | Generate outreach message for a prospect |
| GET | `/api/outreach/history/` | Past generated messages |

---

## Search Configuration Schema

When a user creates a search, they define:

```json
{
  "name": "My Django + Claude Code search",
  "stack_requirements": {
    "must_have": ["django", "claude"],
    "nice_to_have": ["langchain", "react", "typescript", "postgresql"],
    "ai_tool_signals": ["CLAUDE.md", ".cursor", ".github/copilot"]
  },
  "filters": {
    "org_only": true,
    "min_stars": 0,
    "min_contributors": 2,
    "updated_within_days": 180,
    "require_docker": false,
    "require_ci_cd": false,
    "require_tests": false
  },
  "max_results": 50
}
```

---

## Stack Detection Logic

### Python (check in order, stop at first found)
1. `requirements.txt` (or `requirements/base.txt`, `requirements/production.txt`)
2. `pyproject.toml`
3. `Pipfile`
4. `setup.py` / `setup.cfg`

### JavaScript/TypeScript
1. `package.json` (root)
2. `frontend/package.json`, `client/package.json`, `web/package.json`

### AI Tool Signals
| File | Signal |
|------|--------|
| `CLAUDE.md` | Claude Code |
| `.claude/settings.json` | Claude Code |
| `.cursor/` directory | Cursor |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `.windsurfrules` | Windsurf |

### Infrastructure Signals
| File/Directory | Signal |
|----------------|--------|
| `Dockerfile`, `docker-compose.yml` | Docker (production-ready) |
| `.github/workflows/` | CI/CD |
| `tests/`, `test/`, `pytest.ini`, `conftest.py`, `jest.config.*` | Test suite |
| `Procfile`, `railway.json`, `fly.toml`, `render.yaml` | Deployed platform |
| `.env.example`, `.env.production` | Environment config |
| `sentry.properties`, `sentry.client.config.*` | Error monitoring |

---

## Scoring Algorithm

Each prospect is scored 0-100 based on:

| Category | Max Points | Criteria |
|----------|-----------|----------|
| Stack match | 40 | 8 points per must_have tech matched, 4 per nice_to_have |
| AI tool signal | 20 | CLAUDE.md, .cursor, copilot instructions found |
| Production signals | 20 | Docker (5), CI/CD (5), Tests (5), Deployment config (5) |
| Activity | 10 | Updated within 30d (10), 90d (7), 180d (4) |
| Team size | 10 | 5+ contributors (10), 3-4 (7), 2 (4) |

---

## Environment Variables

```bash
# Django
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=

# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# Encryption key for API key storage
FIELD_ENCRYPTION_KEY=

# Google OAuth (account creation)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# GitHub OAuth (connected service for API access)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Claude API (for resume parsing + outreach generation)
ANTHROPIC_API_KEY=

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=30
REFRESH_TOKEN_LIFETIME_DAYS=7
```

Note: Hunter and Apollo API keys are per-user (BYOK), NOT server-level env vars. GitHub access tokens are obtained per-user via OAuth.

---

## Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev

# Services
docker-compose up redis postgres  # Local Redis + Postgres
celery -A config worker -l info   # Background tasks
```

---

## Testing Strategy — TDD

**Test-Driven Development is the standard for this project.** Write the test first, watch it fail, write the code, watch it pass.

### Architecture for Testability
- **Business logic lives in pure functions** — stack detection, scoring, search filtering go in dedicated modules (e.g. `search/detection.py`, `search/scoring.py`), NOT in views or serializers
- **Provider adapters are injectable** — views/tasks receive a provider instance, tests inject mocks
- **Django views are thin** — validate input, call business logic, return response. No logic in views.

### What Gets Tested
| Layer | What | How |
|-------|------|-----|
| Stack detection | Parse requirements.txt, package.json, pyproject.toml → detected techs | Unit tests with fixture files (real dependency files from known projects) |
| Scoring algorithm | Input signals → score 0-100 | Unit tests with edge cases (empty stack, perfect match, partial match) |
| Provider adapters | GitHub/Hunter/Apollo API calls | Unit tests with mocked responses (requests-mock or responses library) |
| Celery tasks | Scan/enrich/parse workflows | Unit tests with mocked providers, test task execution |
| API endpoints | Request → response contract | DRF test client, factory_boy for model fixtures |
| Resume parsing | PDF/DOCX → structured JSON | Unit tests with sample resume files + mocked Claude response |
| Outreach generation | Prospect + profile → message | Unit tests with mocked Claude response |

### Testing Tools
- **pytest** + **pytest-django** — test runner
- **factory_boy** — model factories
- **responses** or **requests-mock** — HTTP mocking for external APIs
- **freezegun** — time-dependent tests (cache TTLs, "updated within X days")
- **Hunter test-api-key** — integration test development against real API with dummy responses

### Test Organization
```
backend/
├── tests/
│   ├── conftest.py           # Shared fixtures, factories
│   ├── fixtures/             # Sample dependency files, API responses
│   │   ├── requirements_django_langchain.txt
│   │   ├── package_react_typescript.json
│   │   ├── github_code_search_response.json
│   │   ├── hunter_domain_search_response.json
│   │   └── sample_resume.pdf
│   ├── test_detection.py     # Stack detection pure functions
│   ├── test_scoring.py       # Scoring algorithm
│   ├── test_github_client.py # GitHub adapter with mocked responses
│   ├── test_hunter.py        # Hunter adapter with mocked responses
│   ├── test_apollo.py        # Apollo adapter with mocked responses
│   ├── test_search_api.py    # Search endpoint integration
│   ├── test_prospects_api.py # Prospects endpoint integration
│   ├── test_enrichment.py    # Enrichment workflow
│   ├── test_resume_parsing.py # Resume upload + parsing
│   └── test_outreach.py      # Message generation
```

### TDD Workflow Per Feature
1. Write a failing test that describes the expected behavior
2. Run `pytest` — confirm it fails for the right reason
3. Write the minimum code to pass
4. Refactor if needed, re-run tests
5. Commit with a message referencing the test: `feat: stack detection for requirements.txt (test_detection.py)`

### Coverage Target
- 90%+ on business logic (detection, scoring, provider adapters)
- 80%+ on API endpoints
- No coverage requirement on Django admin, migrations, or config files

---

## Key Principles
1. **TDD is non-negotiable** — write the test first, then the code. Business logic lives in pure functions, views are thin.
2. **Cache everything** — never hit an external API twice for the same data within TTL
3. **Free endpoint first** — always call Hunter Email Count (free) before Domain Search (costs credits)
4. **Graceful degradation** — if a user has no Hunter key, the app still works (GitHub data only)
5. **Provider-agnostic** — enrichment module uses adapters, easy to add new providers
6. **User controls their data** — can delete resume, API keys, and all prospect data anytime
7. **Background processing** — all multi-step API workflows run in Celery, frontend polls or subscribes for updates
8. **Document everything** — every architecture decision, bug fix, and lesson learned goes in BUILD_LOG.md for LinkedIn/Substack content
