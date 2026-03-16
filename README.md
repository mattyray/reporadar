# RepoRadar

Find companies building with your tech stack, discover matching job openings, and generate personalized outreach — all from one tool.

**Live at [reporadar-app.netlify.app](https://reporadar-app.netlify.app)**

## What It Does

RepoRadar scans GitHub to find companies using specific technologies, then aggregates job listings from multiple sources and matches them against your resume.

1. **Search GitHub** — Find orgs and repos by tech stack (Django + React, MERN + Copilot, whatever). Detects dependencies from `requirements.txt`, `package.json`, `pyproject.toml`, `Gemfile`, `go.mod`, and more.
2. **Detect AI Tools** — Identifies 14+ AI development tools (Claude Code, Cursor, Copilot, Windsurf, Cline, Aider, etc.) from config files.
3. **Score & Rank** — Prospects scored 0-100 on stack match, production signals (Docker, CI/CD, tests, deployment configs), activity, and team size.
4. **Aggregate Jobs** — Pulls job listings from 4 ATS platforms (Greenhouse, Lever, Ashby, Workable) and 4 job boards (RemoteOK, Remotive, We Work Remotely, HN Hiring). Filter by tech, location, remote region, recency, and more.
5. **Match to Resume** — Upload your resume, Claude API extracts your tech stack, and jobs are auto-matched daily.
6. **Enrich Contacts** — Pull business emails and hiring manager contacts via Hunter.io (BYOK).
7. **Generate Outreach** — AI-generated personalized emails and LinkedIn DMs that reference shared stack, open roles, and specific projects.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5, Django REST Framework, Celery + Redis |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache | Redis |
| AI | Claude API (resume parsing, outreach generation) |
| Auth | django-allauth (Google OAuth + GitHub OAuth, headless JWT) |
| External APIs | GitHub REST API v3, Hunter.io, Greenhouse, Lever, Ashby, Workable, RemoteOK, Remotive, WWR |
| Analytics | Built-in (session tracking, GeoIP, bot detection) |
| Backend Hosting | Railway |
| Frontend Hosting | Netlify |

## Features

### Jobs Dashboard (`/dashboard`)
The main view. Aggregated job listings from ATS boards and job boards, with filters for source, tech stack, location (remote region, country, city), department, title, and recency. Jobs auto-refresh on a schedule via Celery Beat.

### GitHub Company Search (`/companies`)
Search GitHub for organizations using specific technologies. Results show detected tech stacks, AI tool signals, infrastructure indicators, and a match score. Click into any company for full detail — repos, contributors, open jobs, and contact info.

### Company Detail (`/prospects/:id`)
Aggregated view of an organization: all repos with detected stacks, top contributors, open job listings from ATS boards, and enriched contact data (if Hunter.io key provided).

### Resume & Job Matching (`/settings`)
Upload a PDF or DOCX resume. Claude API extracts your tech stack and experience. Jobs are automatically matched against your profile daily at 9am UTC.

### AI Outreach (`/prospects/:id`)
Generate personalized email or LinkedIn DM copy for any company. Uses your resume profile + company's detected stack + their open roles as context.

### Settings (`/settings`)
Connect GitHub (OAuth), add Hunter.io/Apollo.io API keys, upload resume, manage account.

## Architecture

```
reporadar/
├── backend/
│   ├── apps/
│   │   ├── accounts/        # User profile, API key management
│   │   ├── search/          # GitHub search, stack detection, scoring
│   │   ├── prospects/       # Organization/repo data, saved lists, export
│   │   ├── jobs/            # ATS probing, job board aggregation, job search
│   │   ├── resumes/         # Resume upload, parsing, job matching
│   │   ├── enrichment/      # Hunter.io contact enrichment
│   │   ├── outreach/        # AI message generation
│   │   └── analytics/       # Session tracking, page views, GeoIP
│   ├── providers/           # API adapters (GitHub, Hunter, ATS, job boards)
│   ├── config/              # Django settings, URLs, Celery config
│   └── tests/               # pytest suite (18 test files)
├── frontend/
│   ├── src/
│   │   ├── app/             # Pages (Jobs, Search, ProspectDetail, Settings, Landing)
│   │   ├── components/      # Layout, SetupChecklist, TechChips, ResumeUploadBanner
│   │   ├── hooks/           # useAuth (JWT management)
│   │   ├── lib/             # API client
│   │   └── types/           # TypeScript interfaces
│   └── netlify.toml         # Rewrites to Railway backend
├── docker-compose.yml       # Local dev (Django, Celery, Postgres, Redis)
└── CLAUDE.md                # Full project specification
```

## Authentication

- **Sign up** with Google OAuth (one click)
- **Connect GitHub** in settings for search access (read-only public repos/orgs)
- **Add Hunter.io key** in settings for contact enrichment (BYOK)
- All credentials encrypted at rest with Fernet

## Development Setup

```bash
# With Docker (recommended)
docker-compose up

# Or manually:

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in values
python manage.py migrate
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Workers (separate terminal)
celery -A config worker --beat -l info
```

### Required Environment Variables

```
SECRET_KEY, DATABASE_URL, REDIS_URL, FIELD_ENCRYPTION_KEY
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
ANTHROPIC_API_KEY  # For resume parsing + outreach
```

Hunter.io and Apollo.io keys are per-user (entered in settings), not server-level.

## Deployment

- **Backend:** Railway (Docker, gunicorn + Celery in same container via `start.sh`)
- **Frontend:** Netlify (auto-deploy from GitHub, SPA with rewrites to Railway)
- **Celery Beat:** 6 scheduled tasks (ATS refresh, job board fetches, resume matching)

## Docs

- [CLAUDE.md](CLAUDE.md) — Full project specification
- [SKILLS.md](SKILLS.md) — Technical skills demonstrated
- [BUILD_LOG.md](BUILD_LOG.md) — Architecture decisions and learnings
